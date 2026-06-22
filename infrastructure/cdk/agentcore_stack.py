from aws_cdk import Stack, Duration, CfnOutput, RemovalPolicy, aws_lambda as _lambda, aws_apigateway as apigw, aws_dynamodb as dynamodb, aws_s3 as s3, aws_iam as iam, aws_cloudwatch as cloudwatch, aws_oudwatch_actions as cw_actions, aws_sns as sns, aws_secretsmanager as secrets, aws_kms as kms
from constructs import Construct

class AgentCoreStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str = "dev", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.env_name = env_name

        self.kms_key = kms.Key(self, "AgentKmsKey", description=f"KMS key for AgentCore - {env_name}", enable_key_rotation=True, removal_policy=RemovalPolicy.DESTROY if env_name == "dev" else RemovalPolicy.RETAIN)
        self.api_keys_secret = secrets.Secret(self, "ApiKeysSecret", secret_name=f"agentcore/api-keys-{env_name}", encryption_key=self.kms_key, removal_policy=RemovalPolicy.DESTROY if env_name == "dev" else RemovalPolicy.RETAIN)
        
        self.logs_bucket = s3.Bucket(self, "AgentLogsBucket", bucket_name=f"agentcore-logs-{self.account}-{env_name}", encryption=s3.BucketEncryption.KMS, encryption_key=self.kms_key, versioned=True, removal_policy=RemovalPolicy.DESTROY if env_name == "dev" else RemovalPolicy.RETAIN, auto_delete_objects=env_name == "dev")
        
        self.customers_table = dynamodb.Table(self, "CustomersTable", table_name=f"agentcore-customers-{env_name}", partition_key=dynamodb.Attribute(name="customer_id", type=dynamodb.AttributeType.STRING), sort_key=dynamodb.Attribute(name="email", type=dynamodb.AttributeType.STRING), billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST, encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED, encryption_key=self.kms_key, point_in_time_recovery=True, removal_policy=RemovalPolicy.DESTROY if env_name == "dev" else RemovalPolicy.RETAIN)
        self.customers_table.add_global_secondary_index(index_name="EmailIndex", partition_key=dynamodb.Attribute(name="email", type=dynamodb.AttributeType.STRING), projection_type=dynamodb.ProjectionType.ALL)
        
        self.conversations_table = dynamodb.Table(self, "ConversationsTable", table_name=f"agentcore-conversations-{env_name}", partition_key=dynamodb.Attribute(name="session_id", type=dynamodb.AttributeType.STRING), sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.NUMBER), billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST, encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED, encryption_key=self.kms_key, time_to_live_attribute="ttl", removal_policy=RemovalPolicy.DESTROY if env_name == "dev" else RemovalPolicy.RETAIN)
        
        self.agent_lambda = _lambda.Function(self, "AgentFunction", function_name=f"agentcore-handler-{env_name}", runtime=_lambda.Runtime.PYTHON_3_11, handler="handler_production.lambda_handler", code=_lambda.Code.from_asset("../../src"), timeout=Duration.seconds(60), memory_size=512, environment={"ENV_NAME": env_name, "CUSTOMERS_TABLE": self.customers_table.table_name, "CONVERSATIONS_TABLE": self.conversations_table.table_name, "LOGS_BUCKET": self.logs_bucket.bucket_name, "API_KEYS_SECRET_ARN": self.api_keys_secret.secret_arn, "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0", "MAX_ITERATIONS": "5"}, tracing=_lambda.Tracing.ACTIVE)
        
        self.kms_key.grant_decrypt(self.agent_lambda)
        self.customers_table.grant_read_write_data(self.agent_lambda)
        self.conversations_table.grant_read_write_data(self.agent_lambda)
        self.logs_bucket.grant_put(self.agent_lambda)
        self.api_keys_secret.grant_read(self.agent_lambda)
        
        self.agent_lambda.add_to_role_policy(iam.PolicyStatement(
            # Added Converse/ConverseStream permissions for the new API
            actions=[
                "bedrock:InvokeModel", 
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:Converse",
                "bedrock:ConverseStream"
            ],
            resources=[f"arn:aws:bedrock:{self.region}::foundation-model/zai.glm-4.7-flash"]
        ))
        
        self.api = apigw.LambdaRestApi(self, "AgentApi", handler=self.agent_lambda, proxy=True, deploy_options=apigw.StageOptions(stage_name=env_name, tracing_enabled=True))
        
        alerts_topic = sns.Topic(self, "AlertsTopic", topic_name=f"agentcore-alerts-{env_name}")
        lambda_errors = self.agent_lambda.metric_errors(period=Duration.minutes(5), statistic="Sum")
        cloudwatch.Alarm(self, "LambdaErrorAlarm", metric=lambda_errors, threshold=5, evaluation_periods=2).add_alarm_action(cw_actions.SnsAction(alerts_topic))
        
        CfnOutput(self, "ApiUrl", value=self.api.url)