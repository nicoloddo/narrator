# Setting Up AWS Access Keys for Narrator

This guide explains how to create and configure AWS access keys for the narrator's S3 storage feature.

## Option 1: Create IAM User (Recommended for Production)

### 1. Create an IAM User

1. Log into AWS Console and go to IAM service
2. Click "Users" → "Create user"
3. Enter details:
   - Name: `narrator-frames`
   - Access type: ✓ Programmatic access

### 2. Create Custom Policy

1. Go to IAM → Policies → Create Policy
2. Use JSON editor and paste:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name/*",
                "arn:aws:s3:::your-bucket-name"
            ]
        }
    ]
}
```
3. Replace `your-bucket-name` with your actual S3 bucket name
4. Name the policy: `NarratorFramesAccess`

### 3. Attach Policy to User

1. Return to your IAM user
2. Click "Attach existing policies"
3. Search for and select `NarratorFramesAccess`
4. Complete user creation
5. **IMPORTANT**: Save the Access Key ID and Secret Access Key shown - you won't see them again!

### 4. Configure Narrator

Add to your environment file:
```bash
USE_S3_STORAGE=true
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_DEFAULT_REGION=your_region  # e.g., us-east-1
S3_BUCKET_NAME=your-bucket-name
```

## Option 2: Use AWS CLI Profile (Development)

If you already have AWS CLI installed and configured:

1. Configure AWS CLI if not done:
```bash
aws configure
```

2. Create named profile for narrator:
```bash
aws configure --profile narrator
```

3. Use profile in environment:
```bash
AWS_PROFILE=narrator
USE_S3_STORAGE=true
S3_BUCKET_NAME=your-bucket-name
```

## Option 3: Use EC2 Instance Role (Production on AWS)

If running on EC2:

1. Create IAM Role:
   - Go to IAM → Roles → Create Role
   - Select EC2 as the service
   - Attach the same policy as above
   - Name it `NarratorFramesRole`

2. Attach to EC2:
   - Select your EC2 instance
   - Actions → Security → Modify IAM Role
   - Select `NarratorFramesRole`

3. Configure narrator (no keys needed):
```bash
USE_S3_STORAGE=true
S3_BUCKET_NAME=your-bucket-name
```

## Security Best Practices

1. **Never commit access keys** to version control
2. Use environment variables or AWS profiles
3. Rotate keys regularly
4. Use least-privilege permissions
5. Consider using AWS Secrets Manager for key storage

## Validating Setup

Test your configuration:

```bash
# Using environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=your_region
export S3_BUCKET_NAME=your-bucket
export USE_S3_STORAGE=true

# Run narrator
python narrator.py
```

Or create a `.env` file:
```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=your_region
S3_BUCKET_NAME=your-bucket
USE_S3_STORAGE=true
```

## Troubleshooting

### Common Issues

1. **"Unable to locate credentials"**
   - Check environment variables are set
   - Verify AWS CLI configuration
   - Check IAM role (if on EC2)

2. **"Access Denied"**
   - Verify policy permissions
   - Check bucket name matches policy
   - Ensure bucket exists in specified region

3. **"Invalid region"**
   - Set `AWS_DEFAULT_REGION`
   - Use valid region identifier (e.g., us-east-1)

### Testing Access

Test S3 access with:
```python
import boto3
import json

def test_s3_access(bucket_name):
    try:
        # Create S3 client
        s3 = boto3.client('s3')
        
        # Test list bucket
        s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        print("✅ Can list bucket")
        
        # Test upload
        s3.put_object(
            Bucket=bucket_name,
            Key='test.txt',
            Body='test'
        )
        print("✅ Can upload to bucket")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

# Run test
test_s3_access('your-bucket-name')
```

## Key Rotation

Regularly rotate your access keys:

1. Create new access key in IAM
2. Update application configuration
3. Test with new key
4. Delete old access key

AWS recommends rotating keys every 90 days. 