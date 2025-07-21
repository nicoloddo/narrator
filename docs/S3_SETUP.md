# S3 Storage Setup for Narrator Frames

The narrator camera system can now save frames directly to Amazon S3 instead of local storage.

## Configuration

### Environment Variables

Add the following environment variables to enable S3 storage:

```bash
# Enable S3 storage
USE_S3_STORAGE=true

# S3 bucket configuration
S3_BUCKET_NAME=your-narrator-frames-bucket
S3_KEY_PREFIX=narrator-frames

# AWS credentials (or use IAM roles/profiles)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1
```

### S3 Key Structure

Frames are organized in S3 with the following structure:
```
s3://your-bucket/narrator-frames/YYYY/MM/DD/HH/frame_123.jpg
s3://your-bucket/narrator-frames/YYYY/MM/DD/HH/movement_frame_456.jpg
```

Examples:
- `s3://narrator-bucket/narrator-frames/2024/03/15/14/frame_001.jpg`
- `s3://narrator-bucket/narrator-frames/2024/03/15/14/movement_frame_025.jpg`

## AWS Setup

### 1. Create S3 Bucket

```bash
aws s3 mb s3://your-narrator-frames-bucket --region us-east-1
```

### 2. Set Bucket Policy (Optional)

For automated cleanup, you can set lifecycle policies:

```json
{
    "Rules": [
        {
            "ID": "DeleteOldFrames",
            "Status": "Enabled",
            "Filter": {
                "Prefix": "narrator-frames/"
            },
            "Expiration": {
                "Days": 30
            }
        }
    ]
}
```

### 3. IAM Permissions

Your AWS credentials need the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": "arn:aws:s3:::your-narrator-frames-bucket/*"
        }
    ]
}
```

## Features

### ✅ **Automatic Organization**
- Frames organized by year/month/day/hour
- Easy to browse and manage

### ✅ **Metadata**
- Each frame includes metadata:
  - `source: narrator-camera`
  - `timestamp: ISO format timestamp`

### ✅ **Fallback Protection** 
- If S3 upload fails, automatically falls back to local storage
- No frame loss even during network issues

### ✅ **Quality Optimization**
- Frames saved as JPEG with 85% quality
- Optimized file size for storage costs

## Local Storage (Default)

If `USE_S3_STORAGE=false` or not set, frames save locally to the `frames/` directory as before.

## Troubleshooting

### Common Issues

**"S3_BUCKET_NAME environment variable is required"**
- Set the `S3_BUCKET_NAME` environment variable

**"Failed to initialize S3 client"**
- Check AWS credentials are properly configured
- Verify AWS region is correct
- Ensure boto3 is installed: `pip install boto3`

**"Failed to save frame to S3"**
- Check internet connectivity
- Verify S3 bucket exists and is accessible
- Check IAM permissions
- System will automatically fall back to local storage

### Testing S3 Connection

You can test your S3 configuration:

```python
import boto3

# Test basic S3 connection
s3 = boto3.client('s3')
try:
    s3.head_bucket(Bucket='your-narrator-frames-bucket')
    print("✅ S3 bucket accessible")
except Exception as e:
    print(f"❌ S3 error: {e}")
```

## Cost Considerations

- Standard S3 storage: ~$0.023 per GB per month
- Consider using S3 Intelligent Tiering for automatic cost optimization
- Set lifecycle policies to automatically delete old frames 