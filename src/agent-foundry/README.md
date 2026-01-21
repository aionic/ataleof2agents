# Azure AI Foundry Workflow Deployment

This directory contains the **declarative workflow configuration** for deploying the Weather Clothing Advisor agent to Azure AI Foundry using YAML-based workflow orchestration.

## 📁 Files

### Configuration Files
- **`agent.yaml`** - Agent configuration (model, tools, instructions, telemetry)
- **`workflow.yaml`** - Workflow orchestration (steps, validation, error handling)
- **`deploy_workflow.py`** - Python deployment script for YAML-based workflows
- **`register_agent.py`** - Legacy programmatic registration (kept for reference)
- **`.env.example`** - Environment variables template

### Contract Files (Referenced)
- `../../specs/001-weather-clothing-advisor/contracts/agent-prompts.md` - Agent system instructions
- `../../specs/001-weather-clothing-advisor/contracts/weather-function-tool.json` - Tool schema

---

## 🚀 Quick Start

### Prerequisites

1. **Azure Resources**:
   - Azure AI Foundry project created
   - Weather Function deployed and accessible
   - Application Insights configured

2. **Environment Variables**:
   ```bash
   # Copy template and fill in your values
   cp .env.example .env

   # Required variables:
   AZURE_AI_PROJECT_ENDPOINT=https://your-project.cognitiveservices.azure.com/
   AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4
   WEATHER_FUNCTION_URL=https://your-function.azurewebsites.net/api/get_weather
   APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=your-key
   ```

3. **Python Dependencies**:
   ```bash
   # All dependencies installed via uv sync (run from repo root)
   uv sync
   ```

### Deploy Workflow

```bash
# Validate configuration
python deploy_workflow.py validate

# Deploy workflow to Foundry
python deploy_workflow.py deploy

# Deploy with custom name
python deploy_workflow.py deploy --workflow-name my-weather-advisor
```

### Manage Workflow

```bash
# List all deployed workflows
python deploy_workflow.py list

# Update existing workflow
python deploy_workflow.py update --agent-id <agent-id>

# Delete workflow
python deploy_workflow.py delete --agent-id <agent-id>
```

---

## 📋 Workflow Configuration

### agent.yaml Structure

```yaml
name: WeatherClothingAdvisor
model:
  deployment_name: ${AZURE_AI_MODEL_DEPLOYMENT_NAME}
  temperature: 0.7
instructions_file: ../../specs/.../agent-prompts.md
tools:
  - name: get_weather
    type: function
    url: ${WEATHER_FUNCTION_URL}
    parameters: {...}
telemetry:
  enabled: true
  application_insights: {...}
settings:
  timeout_seconds: 5
  enable_conversation_history: true
```

### workflow.yaml Structure

```yaml
name: weather-clothing-advisor-workflow
workflow:
  agent: WeatherClothingAdvisor
  type: conversational
steps:
  - parse_user_input
  - get_weather_data
  - generate_recommendations
  - format_response
performance:
  max_duration_seconds: 5
validation:
  response_time: {max_seconds: 5}
  recommendation_count: {min: 3, max: 5}
```

---

## 🔄 Workflow Steps

The workflow orchestrates the following steps:

1. **Parse User Input** - Extract zip code from natural language query
2. **Get Weather Data** - Call weather function with zip code
3. **Generate Recommendations** - Analyze weather and create clothing suggestions
4. **Format Response** - Present recommendations in user-friendly format

Each step is tracked with telemetry for observability.

---

## 🎯 Success Criteria Validation

The workflow enforces all success criteria defined in the specification:

| Criterion | Enforcement | Configuration |
|-----------|-------------|---------------|
| **SC-001**: Response <5s | Workflow timeout | `performance.max_duration_seconds: 5` |
| **SC-002**: 3-5 recommendations | Validation rule | `validation.recommendation_count: {min: 3, max: 5}` |
| **SC-003**: Accurate weather | Tool configuration | `tools[get_weather].timeout_seconds: 5` |
| **SC-004**: Understandable language | Agent instructions | Loaded from `agent-prompts.md` |
| **SC-005**: Re-lookup support | Session tracking | `settings.enable_conversation_history: true` |

---

## 📊 Telemetry & Monitoring

### Application Insights Integration

The workflow automatically tracks:
- **Workflow events**: start, complete, error
- **Tool calls**: get_weather invocations with response times
- **Agent responses**: token usage, response times
- **Custom dimensions**:
  - `deployment_type: foundry-agent`
  - `workflow_version: 1.0.0`
  - `environment: production`

### Viewing Telemetry

```kql
// Application Insights query for workflow metrics
traces
| where customDimensions.deployment_type == "foundry-agent"
| project timestamp, message, customDimensions
| order by timestamp desc
```

---

## 🔧 Configuration Management

### Environment Variables

The YAML files support environment variable substitution:

```yaml
# Syntax: ${VAR_NAME} or ${VAR_NAME:default_value}
model:
  deployment_name: ${AZURE_AI_MODEL_DEPLOYMENT_NAME}

environment: ${ENVIRONMENT:production}
```

### Updating Configuration

1. **Edit YAML files**: Modify `agent.yaml` or `workflow.yaml`
2. **Validate**: Run `python deploy_workflow.py validate`
3. **Update deployment**: Run `python deploy_workflow.py update --agent-id <id>`

---

## 🧪 Testing

### Local Validation

```bash
# Validate YAML syntax and configuration
python deploy_workflow.py validate

# Check environment variables
python -c "import os; print('✓ OK' if os.getenv('AZURE_AI_PROJECT_ENDPOINT') else '✗ Missing AZURE_AI_PROJECT_ENDPOINT')"
```

### End-to-End Testing

After deployment, test the workflow:

```bash
# Using the manual test script
cd ../../tests/manual
python manual_test.py foundry https://your-foundry-endpoint.azure.com
```

---

## 🆚 Deployment Comparison

| Aspect | Workflow (YAML) | Programmatic (register_agent.py) |
|--------|-----------------|----------------------------------|
| **Configuration** | Declarative YAML | Python code |
| **Version Control** | Easy to track | Mixed with logic |
| **Validation** | Built-in | Manual |
| **Orchestration** | Multi-step workflow | Single agent |
| **Recommended** | ✅ Yes (POC standard) | Legacy approach |

---

## 🐛 Troubleshooting

### Common Issues

**"Environment variable not set"**
```bash
# Check your .env file has all required variables
cat .env | grep -v '^#'
```

**"Instructions file not found"**
```bash
# Verify the relative path in agent.yaml
ls ../../specs/001-weather-clothing-advisor/contracts/agent-prompts.md
```

**"Authentication failed"**
```bash
# Ensure Azure credentials are configured
az login
az account show
```

### Debug Mode

Enable debug logging:
```bash
export DEBUG=true
python deploy_workflow.py deploy
```

---

## 📚 Additional Resources

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-foundry/)
- [Agent Framework SDK](https://learn.microsoft.com/azure/ai-services/agents/)
- [Workflow YAML Schema](https://learn.microsoft.com/azure/ai-foundry/workflows)
- [Main Project README](../../README.md)
- [Deployment Guide](../../deploy/README.md)

---

## 🤝 Contributing

When modifying the workflow:

1. Update YAML files with your changes
2. Run validation: `python deploy_workflow.py validate`
3. Test locally if possible
4. Update this README with new features
5. Document any new environment variables in `.env.example`

---

## 📝 Notes

- This workflow follows the **POC Constitution** principles (Simplicity, Documentation-Driven, Rapid Validation)
- All configuration is externalized for easy customization
- Telemetry is automatically integrated for observability
- The workflow enforces all success criteria from the specification
- Both Container Apps and Foundry deployments share the same weather function

**Status**: ✅ Ready for deployment with YAML-based workflow orchestration
