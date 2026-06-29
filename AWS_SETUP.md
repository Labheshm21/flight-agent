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

For a longer-running deployment, run Streamlit through `systemd`, `tmux`, or `screen`.
