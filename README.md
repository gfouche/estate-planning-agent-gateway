# Estate Planning Agent Gateway

A gateway service for estate planning agents using AWS Bedrock Agent Core.

## Overview

This project provides a gateway service for estate planning agents, handling authentication, agent configuration, and communication with AWS Bedrock Agent Core.

## Setup

### Prerequisites

- Python 3.10+
- AWS CLI configured with appropriate credentials
- AWS Bedrock access

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/gfouche/estate-planning-agent-gateway.git
   cd estate-planning-agent-gateway
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   
   # Linux/MacOS
   python -m venv venv
   source venv/bin/activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up the required environment variables:
   ```
   # AWS Configuration
   AWS_REGION=us-east-1
   
   # Cognito Configuration
   COGNITO_USER_POOL_ID=your-user-pool-id
   COGNITO_CLIENT_ID=your-client-id
   COGNITO_CLIENT_SECRET=your-client-secret
   
   # Gateway Configuration
   GATEWAY_URL=your-gateway-url
   M2M_PROVIDER_NAME=gateway-m2m-provider
   ```

## Usage

### Setting up Identity for Token Management

```python
from infrastructure.setup_identity import setup_m2m_credential_provider

# Set up credential provider for gateway access
provider = setup_m2m_credential_provider()
```

### Running the Agent

```
python ep_agent.py
```

## Unit Tests

The project includes a comprehensive unit testing suite. To run the tests, you'll need pytest installed:

```bash
pip install pytest pytest-cov
```

### Running Tests

1. Run all tests in the tests-unit directory:
   ```bash
   cd "C:\Users\Glynn Fouche\Documents\GitHub\estate-planning-agent-gateway"
   & "$pwd\venv\Scripts\python.exe" -m pytest testing\tests-unit\
   ```

2. Run with code coverage to see how much of your code is being tested:
   ```bash
   cd "C:\Users\Glynn Fouche\Documents\GitHub\estate-planning-agent-gateway"
   & "$pwd\venv\Scripts\python.exe" -m pytest testing\tests-unit\ --cov=infrastructure
   ```

3. Generate a detailed coverage report:
   ```bash
   cd "C:\Users\Glynn Fouche\Documents\GitHub\estate-planning-agent-gateway"
   & "$pwd\venv\Scripts\python.exe" -m pytest testing\tests-unit\ --cov=infrastructure --cov-report=html
   ```

4. Run a specific test:
   ```bash
   cd "C:\Users\Glynn Fouche\Documents\GitHub\estate-planning-agent-gateway"
   & "$pwd\venv\Scripts\python.exe" -m pytest testing\tests-unit\test_setup_identity.py::TestSetupIdentity::test_setup_m2m_credential_provider_success -v
   ```

### Test Structure

Tests are organized in the `testing/tests-unit/` directory:
- `test_setup_identity.py` - Tests for the `infrastructure/setup_identity.py` module
- More tests will be added as the project grows

## License

[Specify the license here]

## Contributors

- [List contributors here]
