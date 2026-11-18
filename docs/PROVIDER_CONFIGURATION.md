# Provider Configuration

```toml
[adaptiveai]
local_only = false

[[adaptiveai.cloud_providers]]
provider_id = "my-provider"
deployment_id = "production-us"
base_url = "https://api.provider.example"
api_key_env = "MY_PROVIDER_API_KEY"
permitted_models = ["deployment-a"]
allowed_hosts = ["api.provider.example"]
timeout_seconds = 60
connect_timeout_seconds = 10
max_response_bytes = 2097152

[[adaptiveai.cloud_providers.pricing]]
model = "deployment-a"
input_per_million = 1.0
output_per_million = 2.0
currency = "USD"
source = "provider pricing page; verify for this deployment"
retrieved_at = "YYYY-MM-DD"
```

Set the referenced environment variable outside the TOML file. `providers list` reports only the
reference and whether a value exists; it performs no provider request. Aliases may map friendly
names to allowlisted deployment IDs. Protected payload fields (`model`, `messages`, `stream`, and
authorization) cannot be overridden through request parameters.

Local development servers require `hosted_mode = false`, `allow_localhost = true`, and a localhost
base URL. Do not use these flags in hosted deployments.
