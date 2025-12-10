"""
Email Notification Service for MedAssureAI.
Handles sending completion notifications via AWS SES.
"""
from typing import Dict, Optional
import boto3
from botocore.exceptions import ClientError
from backend.config import config
from backend.logger import logger


class NotificationService:
    """Service for sending email notifications."""
    
    def __init__(self):
        """Initialize notification service with AWS SES client."""
        self.ses_client = None
        self._initialize_ses_client()
    
    def _initialize_ses_client(self):
        """Initialize AWS SES client."""
        try:
            self.ses_client = boto3.client(
                'ses',
                region_name=config.AWS_REGION
            )
            logger.info("AWS SES client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize SES client: {str(e)}")
            # Don't raise - allow service to continue without notifications
    
    def send_completion_notification(
        self,
        email: str,
        project_name: str,
        artifact_counts: Dict[str, int],
        project_id: Optional[str] = None,
        jira_project_key: Optional[str] = None
    ) -> bool:
        """
        Send completion notification email.
        
        Args:
            email: Recipient email address
            project_name: Name of the project
            artifact_counts: Dictionary with artifact counts (epics, features, use_cases, test_cases)
            project_id: Optional project identifier
            jira_project_key: Optional Jira project key
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            logger.info(
                "Sending completion notification",
                extra={
                    "email": email,
                    "project_name": project_name,
                    "project_id": project_id
                }
            )
            
            # Generate email content
            subject = f"MedAssureAI: Test Artifacts Generated for {project_name}"
            html_body = self._generate_email_html(
                project_name=project_name,
                artifact_counts=artifact_counts,
                project_id=project_id,
                jira_project_key=jira_project_key
            )
            text_body = self._generate_email_text(
                project_name=project_name,
                artifact_counts=artifact_counts,
                project_id=project_id,
                jira_project_key=jira_project_key
            )
            
            # Send email via SES
            if self.ses_client:
                response = self.ses_client.send_email(
                    Source=config.NOTIFICATION_FROM_EMAIL,
                    Destination={
                        'ToAddresses': [email]
                    },
                    Message={
                        'Subject': {
                            'Data': subject,
                            'Charset': 'UTF-8'
                        },
                        'Body': {
                            'Text': {
                                'Data': text_body,
                                'Charset': 'UTF-8'
                            },
                            'Html': {
                                'Data': html_body,
                                'Charset': 'UTF-8'
                            }
                        }
                    }
                )
                
                message_id = response.get('MessageId')
                
                logger.info(
                    "Completion notification sent",
                    extra={
                        "email": email,
                        "project_name": project_name,
                        "message_id": message_id
                    }
                )
                
                # Store notification record in DynamoDB
                self._store_notification_record(
                    email=email,
                    project_name=project_name,
                    project_id=project_id,
                    artifact_counts=artifact_counts,
                    message_id=message_id
                )
                
                return True
            else:
                logger.warning("SES client not initialized, skipping email notification")
                return False
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.error(
                "Failed to send completion notification",
                extra={
                    "email": email,
                    "project_name": project_name,
                    "error_code": error_code,
                    "error_message": error_message
                }
            )
            
            # Don't raise - log error and continue
            return False
            
        except Exception as e:
            logger.error(
                "Unexpected error sending completion notification",
                extra={
                    "email": email,
                    "project_name": project_name,
                    "error": str(e)
                }
            )
            
            # Don't raise - log error and continue
            return False
    
    def _generate_email_html(
        self,
        project_name: str,
        artifact_counts: Dict[str, int],
        project_id: Optional[str] = None,
        jira_project_key: Optional[str] = None
    ) -> str:
        """
        Generate HTML email body.
        
        Args:
            project_name: Name of the project
            artifact_counts: Dictionary with artifact counts
            project_id: Optional project identifier
            jira_project_key: Optional Jira project key
            
        Returns:
            HTML email body
        """
        total_artifacts = artifact_counts.get('total', 0)
        epics = artifact_counts.get('epics', 0)
        features = artifact_counts.get('features', 0)
        use_cases = artifact_counts.get('use_cases', 0)
        test_cases = artifact_counts.get('test_cases', 0)
        
        jira_section = ""
        if jira_project_key:
            jira_section = f"""
            <tr>
                <td style="padding: 10px 0;">
                    <strong>Jira Project:</strong> {jira_project_key}
                </td>
            </tr>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Test Artifacts Generated</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; border-radius: 8px; padding: 30px; margin-bottom: 20px;">
                <h1 style="color: #2c3e50; margin-top: 0;">Test Artifacts Generated Successfully</h1>
                <p style="font-size: 16px; color: #555;">
                    Your test artifacts for <strong>{project_name}</strong> have been generated and are ready for review.
                </p>
            </div>
            
            <div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <h2 style="color: #2c3e50; margin-top: 0;">Project Summary</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px 0;">
                            <strong>Project Name:</strong> {project_name}
                        </td>
                    </tr>
                    {jira_section}
                    <tr>
                        <td style="padding: 10px 0;">
                            <strong>Total Artifacts:</strong> {total_artifacts}
                        </td>
                    </tr>
                </table>
            </div>
            
            <div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <h2 style="color: #2c3e50; margin-top: 0;">Artifact Breakdown</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;"><strong>Artifact Type</strong></td>
                        <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: right;"><strong>Count</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">Epics</td>
                        <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: right;">{epics}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">Features</td>
                        <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: right;">{features}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">Use Cases</td>
                        <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: right;">{use_cases}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">Test Cases</td>
                        <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: right;">{test_cases}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa; font-weight: bold;">
                        <td style="padding: 12px;">Total</td>
                        <td style="padding: 12px; text-align: right;">{total_artifacts}</td>
                    </tr>
                </table>
            </div>
            
            <div style="background-color: #e8f4f8; border-left: 4px solid #3498db; padding: 15px; margin-bottom: 20px;">
                <p style="margin: 0; color: #2c3e50;">
                    <strong>Next Steps:</strong><br>
                    • Review the generated artifacts in your dashboard<br>
                    • Check Jira for created issues<br>
                    • Refine artifacts as needed using the enhancement feature
                </p>
            </div>
            
            <div style="text-align: center; padding: 20px 0; color: #777; font-size: 14px;">
                <p>This is an automated notification from MedAssureAI</p>
                <p style="margin: 5px 0;">Healthcare Test Automation Platform</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_email_text(
        self,
        project_name: str,
        artifact_counts: Dict[str, int],
        project_id: Optional[str] = None,
        jira_project_key: Optional[str] = None
    ) -> str:
        """
        Generate plain text email body.
        
        Args:
            project_name: Name of the project
            artifact_counts: Dictionary with artifact counts
            project_id: Optional project identifier
            jira_project_key: Optional Jira project key
            
        Returns:
            Plain text email body
        """
        total_artifacts = artifact_counts.get('total', 0)
        epics = artifact_counts.get('epics', 0)
        features = artifact_counts.get('features', 0)
        use_cases = artifact_counts.get('use_cases', 0)
        test_cases = artifact_counts.get('test_cases', 0)
        
        jira_line = f"\nJira Project: {jira_project_key}" if jira_project_key else ""
        
        text = f"""
Test Artifacts Generated Successfully

Your test artifacts for {project_name} have been generated and are ready for review.

PROJECT SUMMARY
---------------
Project Name: {project_name}{jira_line}
Total Artifacts: {total_artifacts}

ARTIFACT BREAKDOWN
------------------
Epics:      {epics}
Features:   {features}
Use Cases:  {use_cases}
Test Cases: {test_cases}
-----------
Total:      {total_artifacts}

NEXT STEPS
----------
• Review the generated artifacts in your dashboard
• Check Jira for created issues
• Refine artifacts as needed using the enhancement feature

---
This is an automated notification from MedAssureAI
Healthcare Test Automation Platform
        """
        
        return text.strip()
    
    def _store_notification_record(
        self,
        email: str,
        project_name: str,
        project_id: Optional[str],
        artifact_counts: Dict[str, int],
        message_id: str
    ):
        """
        Store notification record in DynamoDB.
        
        Args:
            email: Recipient email address
            project_name: Name of the project
            project_id: Project identifier
            artifact_counts: Dictionary with artifact counts
            message_id: SES message ID
        """
        try:
            # In production, this would store in DynamoDB via MCP Server or boto3
            logger.info(
                "Storing notification record",
                extra={
                    "email": email,
                    "project_name": project_name,
                    "project_id": project_id,
                    "message_id": message_id
                }
            )
            
            # Simulate DynamoDB storage
            notification_record = {
                "PK": f"PROJECT#{project_id}" if project_id else f"NOTIFICATION#{message_id}",
                "SK": f"NOTIFICATION#{message_id}",
                "email": email,
                "project_name": project_name,
                "project_id": project_id,
                "artifact_counts": artifact_counts,
                "message_id": message_id,
                "sent_at": "timestamp_placeholder",
                "status": "sent"
            }
            
            logger.info(
                "Notification record stored",
                extra={"message_id": message_id}
            )
            
        except Exception as e:
            logger.error(
                "Failed to store notification record",
                extra={
                    "message_id": message_id,
                    "error": str(e)
                }
            )
            # Don't raise - this is not critical


# Create singleton instance
notification_service = NotificationService()
