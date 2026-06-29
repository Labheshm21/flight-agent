# AWS Setup

This app can run on EC2 and store completed travel plans in DynamoDB while writing generation events to CloudWatch Logs.

## 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Create the DynamoDB table

Use a simple table keyed by `plan_id`:

```bash
aws dynamodb create-table \
  --table-name TravelPlans \
  --attribute-definitions AttributeName=plan_id,AttributeType=S \
  --key-schema AttributeName=plan_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

## 3. Set environment variables

Create a `.env` file on the EC2 instance:

```bash
GROQ_API_KEY=your_groq_key
AVIATION_API_KEY=your_aviation_key
TAVILY_API_KEY=your_tavily_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

AWS_REGION=us-east-1
TRAVEL_PLANS_TABLE=TravelPlans
CLOUDWATCH_LOG_GROUP=/ai-travel-booking
CLOUDWATCH_LOG_STREAM=streamlit-app
```

## 4. IAM permissions

Attach an IAM role to the EC2 instance with permissions like:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/TravelPlans"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:DescribeLogStreams",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

## 5. Run the app on EC2

```bash
streamlit run frontend.py --server.address 0.0.0.0 --server.port 8501
```

Open port `8501` in the EC2 security group, then visit:

```text
http://EC2_PUBLIC_IP:8501
```

For a longer-running deployment, run Streamlit through `systemd`.

## 6. Run Streamlit with systemd

Copy the included service file into place:

```bash
cd ~/flight-agent
sudo cp deploy/travel-app.service /etc/systemd/system/travel-app.service
sudo systemctl daemon-reload
sudo systemctl enable travel-app
sudo systemctl start travel-app
sudo systemctl status travel-app
```

Useful commands:

```bash
sudo systemctl restart travel-app
sudo journalctl -u travel-app -f
```

## 7. GitHub Actions CI/CD

The workflow in `.github/workflows/deploy-ec2.yml` deploys every push to `main` onto EC2.

Add these GitHub repository secrets:

```text
EC2_HOST=18.224.23.171
EC2_USER=ubuntu
EC2_SSH_KEY=<contents of your flightagent.pem file>
```

The workflow uploads the latest code, keeps `.env`, `.venv`, and `travel_plans/` untouched on EC2, installs dependencies, installs the `systemd` service, and restarts the `travel-app` service.
