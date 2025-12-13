"""
Test script for DynamoDB Tools
Verifies that the DynamoDB tools can store and retrieve test artifacts
"""
import json
from agents.dynamodb_tools import store_test_artifacts_tool, get_project_artifacts_tool


def test_store_artifacts():
    """Test storing test artifacts in DynamoDB"""
    
    # Sample test artifacts structure
    test_epics = [
        {
            "epic_id": "E001",
            "epic_name": "Patient Information Collection",
            "description": "Comprehensive system for collecting, validating, storing, and managing patient information including demographics, medical history, insurance details, and consent documentation in compliance with healthcare regulations.",
            "priority": "Critical",
            "jira_issue_id": None,
            "jira_issue_key": "HS25SKL-1812",
            "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1812",
            "jira_status": "Pushed",
            "review_status": "Approved",
            "model_explanation": "Epic created based on primary requirement for patient onboarding with emphasis on comprehensive information collection that meets HIPAA and healthcare regulatory requirements.",
            "compliance_mapping": [
                "HIPAA Privacy Rule",
                "HIPAA Security Rule",
                "FDA 21 CFR Part 820",
                "ISO 13485:7.5.1",
                "IEC 62304:5.2"
            ],
            "features": [
                {
                "feature_id": "F001",
                "feature_name": "Demographics",
                "description": "Collection and management of patient personal information including name, contact details, date of birth, address, and emergency contacts with appropriate validation and security controls.",
                "priority": "High",
                "jira_issue_id": None,
                "jira_issue_key": "HS25SKL-1813",
                "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1813",
                "jira_status": "Pushed",
                "review_status": "Approved",
                "model_explanation": "Feature derived from primary requirement to gather patient demographic information with emphasis on data completeness and accuracy.",
                "compliance_mapping": [
                    "HIPAA § 164.512",
                    "ISO 13485:7.5.1",
                    "FDA 21 CFR Part 11"
                ],
                "use_cases": [
                    {
                    "use_case_id": "UC001",
                    "title": "Patient Provides Basic Demographic Information",
                    "description": "Patient enters personal identification and contact information into the system with proper validation and verification.",
                    "acceptance_criteria": [
                        "System collects patient's full legal name with appropriate validation",
                        "System captures and validates contact information including phone and email",
                        "System records date of birth in standard format with age calculation",
                        "System validates and formats residential address with postal code validation",
                        "System allows addition of at least two emergency contacts with relationship designation"
                    ],
                    "priority": "Critical",
                    "jira_issue_id": None,
                    "jira_issue_key": "HS25SKL-1845",
                    "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1845",
                    "jira_status": "Pushed",
                    "test_scenarios_outline": [
                        "Verify capture of complete demographic information",
                        "Validate formatting and validation rules for contact information",
                        "Confirm proper storage and retrieval of personal identifiers",
                        "Test emergency contact management functionality",
                        "Verify data protection and encryption measures"
                    ],
                    "model_explanation": "Use case developed from demographic requirements with focus on comprehensive data collection, validation, and secure storage in compliance with patient privacy regulations.",      
                    "review_status": "Approved",
                    "comments": "Core use case for patient registration process with critical HIPAA compliance requirements.",
                    "compliance_mapping": [
                        "HIPAA § 164.512",
                        "ISO 13485:7.5.1",
                        "FDA 21 CFR Part 11",
                        "GDPR Article 6"
                    ],
                    "test_cases": [
                        {
                        "test_case_id": "TC001",
                        "test_case_title": "Complete Demographic Information Submission",
                        "preconditions": [
                            "Patient onboarding module is accessible",
                            "User has appropriate system access",
                            "New patient record initiated"
                        ],
                        "test_steps": [
                            "Navigate to patient demographics entry screen",
                            "Enter valid full legal name (first, middle, last)",
                            "Input valid phone number and email address",
                            "Enter date of birth in MM/DD/YYYY format",
                            "Input complete residential address with zip code",
                            "Add two emergency contacts with names, relationships, and contact information",
                            "Submit the form"
                        ],
                        "expected_result": "System accepts all data, validates formatting, encrypts sensitive information, and creates patient demographic record with confirmation message. All entered data should be properly stored and retrievable.",
                        "test_type": "Functional",
                        "priority": "High",
                        "jira_issue_id": None,
                        "jira_issue_key": "HS25SKL-1850",
                        "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1850",
                        "jira_status": "Pushed",
                        "compliance_mapping": [
                            "HIPAA § 164.312(a)",
                            "ISO 13485:7.5.1",
                            "FDA 21 CFR Part 11"
                        ],
                        "model_explanation": "Test case validates the core demographic data collection functionality with all required fields and proper encryption of PHI per HIPAA Security Rule requirements.",
                        "review_status": "Approved",
                        "comments": "Critical path test for patient registration process."
                        },
                        {
                        "test_case_id": "TC002",
                        "test_case_title": "Invalid Contact Information Validation",
                        "preconditions": [
                            "Patient demographics form is open",
                            "Patient basic information already entered"
                        ],
                        "test_steps": [
                            "Enter malformed email address (missing @ symbol)",
                            "Enter invalid phone number with letters",
                            "Enter zip code with incorrect format",
                            "Attempt to submit the form"
                        ],
                        "expected_result": "System identifies each validation error with specific error messages indicating the exact issue. Form submission is prevented until all errors are corrected. No partial or invalid data should be saved to the database.",
                        "test_type": "Negative",
                        "priority": "Medium",
                        "jira_issue_id": None,
                        "jira_issue_key": "HS25SKL-1851",
                        "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1851",
                        "jira_status": "Pushed",
                        "compliance_mapping": [
                            "HIPAA § 164.312(c)(1)",
                            "ISO 13485:7.5.1",
                            "IEC 62304:5.5.3"
                        ],
                        "model_explanation": "Negative test case validates data integrity controls required by HIPAA to ensure accuracy of PHI and prevent data corruption through validation rules.",
                        "review_status": "Approved",
                        "comments": "Validates system's ability to enforce data quality standards."
                        }
                    ]
                    },
                    {
                    "use_case_id": "UC002",
                    "title": "Patient Updates Demographic Information",
                    "description": "Existing patient modifies previously submitted demographic information with proper change tracking and verification.",
                    "acceptance_criteria": [
                        "System allows authenticated patient to view and modify existing demographic data",
                        "All changes are tracked with timestamp and user information",
                        "Modified information undergoes same validation as initial entry",
                        "System confirms successful updates with notification"
                    ],
                    "priority": "High",
                    "jira_issue_id": None,
                    "jira_issue_key": "HS25SKL-1846",
                    "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1846",
                    "jira_status": "Pushed",
                    "test_scenarios_outline": [
                        "Verify patient can update contact information",
                        "Confirm proper validation of modified data",
                        "Test audit trail creation for data changes",
                        "Verify notification of successful updates"
                    ],
                    "model_explanation": "Use case developed for maintaining accurate patient information over time with focus on data integrity and change management required by healthcare regulations.",
                    "review_status": "Approved",
                    "comments": "Important for long-term patient record management and compliance.",
                    "compliance_mapping": [
                        "HIPAA § 164.526",
                        "ISO 13485:7.5.3",
                        "FDA 21 CFR Part 11"
                    ],
                    "test_cases": [
                        {
                        "test_case_id": "TC003",
                        "test_case_title": "Update Patient Address Information",
                        "preconditions": [
                            "Patient record exists in system",
                            "User is authenticated with appropriate access rights",
                            "Patient demographics screen is accessible"
                        ],
                        "test_steps": [
                            "Search and retrieve existing patient record",
                            "Navigate to demographics section",
                            "Modify current address with new valid address",
                            "Save changes",
                            "Exit and reload patient record"
                        ],
                        "expected_result": "System updates address information, creates audit trail entry with timestamp and user ID, displays confirmation message, and shows updated information when record is reloaded. Previous address is maintained in history.",
                        "test_type": "Functional",
                        "priority": "Medium",
                        "jira_issue_id": None,
                        "jira_issue_key": "HS25SKL-1852",
                        "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1852",
                        "jira_status": "Pushed",
                        "compliance_mapping": [
                            "HIPAA § 164.526",
                            "HIPAA § 164.312(b)",
                            "ISO 13485:7.5.3"
                        ],
                        "model_explanation": "Test case validates update functionality with audit trail requirements specified by HIPAA for modifications to PHI and record keeping.",
                        "review_status": "Approved",
                        "comments": "Confirms system's ability to maintain information currency while preserving modification history."
                        }
                    ]
                    }
                ]
                },
                {
                "feature_id": "F002",
                "feature_name": "Medical History",
                "description": "Collection and management of patient medical history including past and current conditions, allergies, surgical history, and family medical history with appropriate categorization and clinical coding.",
                "priority": "Critical",
                "jira_issue_id": None,
                "jira_issue_key": "HS25SKL-1814",
                "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1814",
                "jira_status": "Pushed",
                "review_status": "Approved",
                "model_explanation": "Feature derived from requirement to collect comprehensive medical history information essential for patient care and treatment planning.",
                "compliance_mapping": [
                    "HIPAA § 164.501",
                    "ISO 13485:7.5.1",
                    "FDA 21 CFR Part 11"
                ],
                "use_cases": [
                    {
                    "use_case_id": "UC003",
                    "title": "Patient Provides Complete Medical History",
                    "description": "Patient enters comprehensive medical history including conditions, allergies, procedures, and family history with appropriate clinical coding and categorization.",
                    "acceptance_criteria": [
                        "System allows entry of current and past medical conditions with onset dates",
                        "System captures medication allergies and reactions with severity indicators",
                        "System records surgical procedures with dates and relevant details",
                        "System documents family medical history with relationship designations",
                        "System supports attaching supporting documentation"
                    ],
                    "priority": "Critical",
                    "jira_issue_id": None,
                    "jira_issue_key": "HS25SKL-1847",
                    "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1847",
                    "jira_status": "Pushed",
                    "test_scenarios_outline": [
                        "Verify capture of comprehensive medical history information",
                        "Test clinical coding integration and validation",
                        "Confirm allergy severity and reaction documentation",
                        "Validate family history relationship mapping",
                        "Test document attachment functionality"
                    ],
                    "model_explanation": "Use case developed from medical history requirements focusing on comprehensive health data collection essential for clinical decision-making and treatment safety.",
                    "review_status": "Approved",
                    "comments": "Critical for patient safety and care planning with specific regulatory requirements.",
                    "compliance_mapping": [
                        "HIPAA § 164.501",
                        "ISO 13485:7.5.1",
                        "FDA 21 CFR Part 11",
                        "IEC 62304:5.2.2"
                    ],
                    "test_cases": [
                        {
                        "test_case_id": "TC004",
                        "test_case_title": "Complete Allergy Information Documentation",
                        "preconditions": [
                            "Patient record exists in system",
                            "Medical history module is accessible",
                            "User has appropriate system access"
                        ],
                        "test_steps": [
                            "Navigate to allergies section in medical history",
                            "Select 'Add New Allergy' option",
                            "Select allergen type from standardized list",
                            "Enter specific allergen information",
                            "Select reaction severity (Mild, Moderate, Severe)",
                            "Document observed reactions",
                            "Enter onset date or approximate timeframe",
                            "Save allergy information"
                        ],
                        "expected_result": "System records allergy information with proper clinical coding, creates appropriate alerts for the documented allergy, and makes the information prominently available in patient summary views with visual indicators for severe allergies.",
                        "test_type": "Functional",
                        "priority": "High",
                        "jira_issue_id": None,
                        "jira_issue_key": "HS25SKL-1853",
                        "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1853",
                        "jira_status": "Pushed",
                        "compliance_mapping": [
                            "HIPAA § 164.312(b)",
                            "ISO 13485:7.5.1",
                            "IEC 62304:5.2.2"
                        ],
                        "model_explanation": "Test case validates the system's ability to properly document patient allergies, which is critical for patient safety and required by clinical documentation standards and healthcare regulations.",
                        "review_status": "Approved",
                        "comments": "Patient safety critical test case with high visibility requirements."
                        },
                        {
                        "test_case_id": "TC005",
                        "test_case_title": "Family Medical History Documentation",
                        "preconditions": [
                            "Patient record exists in system",
                            "Medical history module is accessible",
                            "User has appropriate system access"
                        ],
                        "test_steps": [
                            "Navigate to family history section",
                            "Select 'Add Family History' option",
                            "Select relationship type (parent, sibling, etc.)",
                            "Enter medical condition from standardized list",
                            "Document age of onset if known",
                            "Indicate living/deceased status",
                            "Add multiple conditions for same family member",
                            "Save family history information"
                        ],
                        "expected_result": "System records family medical history with relationship context, allows multiple conditions per family member, supports structured and unstructured entries, and makes information available in genetic risk assessment views.",
                        "test_type": "Functional",
                        "priority": "Medium",
                        "jira_issue_id": None,
                        "jira_issue_key": "HS25SKL-1854",
                        "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1854",
                        "jira_status": "Pushed",
                        "compliance_mapping": [
                            "HIPAA § 164.524",
                            "ISO 13485:7.5.1",
                            "IEC 62304:5.2.2"
                        ],
                        "model_explanation": "Test case validates the system's ability to properly document family medical history, which provides important clinical context for preventative care and risk assessment required by healthcare quality standards.",
                        "review_status": "Approved",
                        "comments": "Important for preventative care planning and risk assessment."
                        }
                    ]
                    }
                ]
                },
                {
                "feature_id": "F003",
                "feature_name": "Insurance Details",
                "description": "Collection and verification of patient insurance information including carrier details, policy and group numbers, subscriber information, and coverage verification.",
                "priority": "High",
                "jira_issue_id": None,
                "jira_issue_key": "HS25SKL-1815",
                "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1815",
                "jira_status": "Pushed",
                "review_status": "Approved",
                "model_explanation": "Feature derived from requirement to accurately collect and verify patient insurance information for billing and claims processing.",
                "compliance_mapping": [
                    "HIPAA § 164.506",
                    "ISO 13485:7.5.1",
                    "FDA 21 CFR Part 11"
                ],
                "use_cases": [
                    {
                    "use_case_id": "UC004",
                    "title": "Patient Provides Insurance Information",
                    "description": "Patient submits insurance policy details with verification against payer databases and coverage determination.",
                    "acceptance_criteria": [
                        "System captures insurance carrier information with validated selection lists",
                        "System records policy, group, and member identification numbers with format validation",
                        "System collects policyholder/subscriber details when patient is not the primary insured",
                        "System supports entry of secondary/supplemental insurance information",
                        "System performs insurance verification against payer databases when available"
                    ],
                    "priority": "High",
                    "jira_issue_id": None,
                    "jira_issue_key": "HS25SKL-1848",
                    "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1848",
                    "jira_status": "Pushed",
                    "test_scenarios_outline": [
                        "Verify capture of primary insurance information",
                        "Test validation rules for policy and group numbers",
                        "Confirm subscriber relationship documentation",
                        "Validate secondary insurance workflow",
                        "Test insurance verification functionality"
                    ],
                    "model_explanation": "Use case developed from insurance information requirements focusing on accurate collection of payer information required for billing and claims processing.",
                    "review_status": "Approved",
                    "comments": "Critical for revenue cycle management and claims processing.",
                    "compliance_mapping": [
                        "HIPAA § 164.506",
                        "ISO 13485:7.5.1",
                        "FDA 21 CFR Part 11"
                    ],
                    "test_cases": [
                        {
                        "test_case_id": "TC006",
                        "test_case_title": "Primary Insurance Information Capture",
                        "preconditions": [
                            "Patient record exists in system",
                            "Insurance module is accessible",
                            "Insurance carrier database is available"
                        ],
                        "test_steps": [
                            "Navigate to insurance information section",
                            "Select 'Add Primary Insurance' option",
                            "Select insurance carrier from validated list",
                            "Enter policy number with proper format",
                            "Enter group number with proper format",
                            "Specify relationship to policyholder (self, spouse, dependent)",
                            "If not self, enter policyholder demographics",
                            "Submit insurance information",
                            "System attempts verification with payer database"
                        ],
                        "expected_result": "System records complete insurance information, validates format of policy and group numbers, associates with appropriate payer rules, and attempts real-time verification when available, displaying coverage status and any error messages.",
                        "test_type": "Functional",
                        "priority": "High",
                        "jira_issue_id": None,
                        "jira_issue_key": "HS25SKL-1855",
                        "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1855",
                        "jira_status": "Pushed",
                        "compliance_mapping": [
                            "HIPAA § 164.506",
                            "ISO 13485:7.5.1",
                            "FDA 21 CFR Part 11"
                        ],
                        "model_explanation": "Test case validates the system's ability to capture insurance information needed for treatment, payment, and healthcare operations as permitted under HIPAA with appropriate data validation.",
                        "review_status": "Approved",
                        "comments": "Critical for financial clearance and claims processing."
                        },
                        {
                        "test_case_id": "TC007",
                        "test_case_title": "Secondary Insurance Information Capture",
                        "preconditions": [
                            "Patient record exists with primary insurance",
                            "Insurance module is accessible",
                            "User has appropriate system access"
                        ],
                        "test_steps": [
                            "Navigate to insurance information section",
                            "Select 'Add Secondary Insurance' option",
                            "Select insurance carrier from validated list",
                            "Enter policy number with proper format",
                            "Enter group number with proper format",
                            "Specify relationship to policyholder",
                            "If not self, enter policyholder demographics",
                            "Indicate coordination of benefits order",
                            "Submit secondary insurance information"
                        ],
                        "expected_result": "System records secondary insurance information, clearly differentiates from primary coverage, establishes correct coordination of benefits order, and maintains relationships between all documented insurance plans.",
                        "test_type": "Functional",
                        "priority": "Medium",
                        "jira_issue_id": None,
                        "jira_issue_key": "HS25SKL-1856",
                        "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1856",
                        "jira_status": "Pushed",
                        "compliance_mapping": [
                            "HIPAA § 164.506",
                            "ISO 13485:7.5.1"
                        ],
                        "model_explanation": "Test case validates the system's ability to handle multiple insurance plans and coordination of benefits requirements for proper claims processing and billing compliance.",    
                        "review_status": "Approved",
                        "comments": "Important for complete coverage documentation and coordination of benefits."
                        }
                    ]
                    }
                ]
                },
                {
                "feature_id": "F004",
                "feature_name": "Consent Forms",
                "description": "Management of electronic patient consent including consent for treatment, acknowledgment of privacy practices, authorization for electronic communications, and other required legal agreements.",
                "priority": "Critical",
                "jira_issue_id": None,
                "jira_issue_key": "HS25SKL-1816",
                "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1816",
                "jira_status": "Pushed",
                "review_status": "Approved",
                "model_explanation": "Feature derived from requirement to obtain and document patient consent in compliance with legal and regulatory requirements for healthcare operations.",
                "compliance_mapping": [
                    "HIPAA § 164.508",
                    "HIPAA § 164.520",
                    "ISO 13485:7.5.1",
                    "FDA 21 CFR Part 11"
                ],
                "use_cases": [
                    {
                    "use_case_id": "UC005",
                    "title": "Patient Provides Electronic Consent",
                    "description": "Patient reviews and electronically signs required consent forms with appropriate documentation and audit trail.",
                    "acceptance_criteria": [
                        "System presents required consent forms with complete legal text",
                        "Patient can review full document content before signing",
                        "System captures electronic signature with proper authentication",
                        "System records consent version, timestamp, and identity verification method",
                        "System provides confirmation and copy of signed documents",
                        "System maintains tamper-evident audit trail of consent process"
                    ],
                    "priority": "Critical",
                    "jira_issue_id": None,
                    "jira_issue_key": "HS25SKL-1849",
                    "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1849",
                    "jira_status": "Pushed",
                    "test_scenarios_outline": [
                        "Verify presentation of consent forms",
                        "Test electronic signature capture",
                        "Confirm consent versioning and tracking",
                        "Validate audit trail creation",
                        "Test consent document retrieval"
                    ],
                    "model_explanation": "Use case developed from consent management requirements focusing on legally compliant electronic signature capture and documentation required by healthcare regulations.",
                    "review_status": "Approved",
                    "comments": "Critical for legal compliance and patient rights protection.",
                    "compliance_mapping": [
                        "HIPAA § 164.508",
                        "HIPAA § 164.520",
                        "ISO 13485:7.5.1",
                        "FDA 21 CFR Part 11"
                    ],
                    "test_cases": [
                        {
                        "test_case_id": "TC008",
                        "test_case_title": "Treatment Consent Electronic Signature",
                        "preconditions": [
                            "Patient record exists in system",
                            "Consent management module is accessible",
                            "Current consent form templates are available"
                        ],
                        "test_steps": [
                            "Navigate to consent management section",
                            "Select 'Treatment Consent' form",
                            "Present full consent document text to patient",
                            "Provide mechanism to scroll through entire document",
                            "Require patient to acknowledge they have read and understood content",
                            "Capture electronic signature using touchscreen or typed name",
                            "Record date, time, and identity verification method",
                            "Generate confirmation with option to download or email copy"
                        ],
                        "expected_result": "System records electronically signed consent with tamper-evident metadata including identity verification method, timestamp, form version, and complete audit trail. Signed consent should be retrievable and printable with visible signature.",
                        "test_type": "Functional",
                        "priority": "Critical",
                        "jira_issue_id": None,
                        "jira_issue_key": "HS25SKL-1857",
                        "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1857",
                        "jira_status": "Pushed",
                        "compliance_mapping": [
                            "HIPAA § 164.508",
                            "FDA 21 CFR Part 11",
                            "ISO 13485:7.5.1",
                            "GDPR Article 7"
                        ],
                        "model_explanation": "Test case validates the system's ability to capture legally binding electronic consent in compliance with HIPAA authorization requirements and FDA electronic signature standards.",
                        "review_status": "Approved",
                        "comments": "Critical legal and compliance requirement for healthcare operations."
                        },
                        {
                        "test_case_id": "TC009",
                        "test_case_title": "Notice of Privacy Practices Acknowledgment",
                        "preconditions": [
                            "Patient record exists in system",
                            "Consent management module is accessible",
                            "Current Notice of Privacy Practices is available"
                        ],
                        "test_steps": [
                            "Navigate to consent management section",
                            "Select 'Notice of Privacy Practices' acknowledgment",
                            "Present complete HIPAA-compliant privacy notice",
                            "Provide mechanism to scroll through entire document",
                            "Capture patient acknowledgment of receipt",
                            "Record date and time of acknowledgment",
                            "Generate confirmation with option for copy"
                        ],
                        "expected_result": "System records patient acknowledgment of privacy practices with timestamp, form version, and audit trail. System should be able to provide evidence of acknowledgment for compliance reporting and make status visible in patient record.",
                        "test_type": "Functional",
                        "priority": "Critical",
                        "jira_issue_id": None,
                        "jira_issue_key": "HS25SKL-1858",
                        "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1858",
                        "jira_status": "Pushed",
                        "compliance_mapping": [
                            "HIPAA § 164.520",
                            "ISO 13485:7.5.1",
                            "FDA 21 CFR Part 11"
                        ],
                        "model_explanation": "Test case validates the system's ability to satisfy HIPAA requirements for providing Notice of Privacy Practices to patients and documenting their acknowledgment with proper record keeping.",
                        "review_status": "Approved",
                        "comments": "Mandatory HIPAA compliance requirement."
                        },
                        {
                        "test_case_id": "TC010",
                        "test_case_title": "Electronic Communication Consent",
                        "preconditions": [
                            "Patient record exists in system",
                            "Consent management module is accessible",
                            "Electronic communication consent template is available"
                        ],
                        "test_steps": [
                            "Navigate to consent management section",
                            "Select 'Electronic Communication' consent form",
                            "Present detailed consent explaining risks of electronic communication",
                            "Allow patient to select preferred communication channels (email, text, patient portal)",
                            "Collect and verify communication addresses/numbers",
                            "Capture patient signature for each selected method",
                            "Record consent with date and time",
                            "Generate confirmation of communication preferences"
                        ],
                        "expected_result": "System records patient's communication preferences with specific consent for each electronic method, maintains audit trail of consent process, and makes preferences available to communication systems with proper security controls.",
                        "test_type": "Functional",
                        "priority": "High",
                        "jira_issue_id": None,
                        "jira_issue_key": "HS25SKL-1859",
                        "jira_issue_url": "https://hsskill.atlassian.net/browse/HS25SKL-1859",
                        "jira_status": "Pushed",
                        "compliance_mapping": [
                            "HIPAA § 164.522",
                            "HIPAA § 164.530",
                            "ISO 13485:7.5.1",
                            "FDA 21 CFR Part 11"
                        ],
                        "model_explanation": "Test case validates the system's ability to obtain specific consent for electronic communications containing PHI as required by HIPAA and document patient preferences for communication methods.",
                        "review_status": "Approved",
                        "comments": "Important for compliant patient communications and engagement."
                        }
                    ]
                    }
                ]
                }
            ]
        }
    ]
    
    # Convert to JSON string
    epics_json = json.dumps(test_epics)
    
    # Test storing artifacts
    print("Testing store_test_artifacts_tool...")
    print("-" * 80)
    
    result = store_test_artifacts_tool(
        project_id="patient_onboarding_specifications_ada08123",
        project_name="Patient Onboarding Specifications",
        session_id="test_session_123",
        epics_json=epics_json,
        jira_project_key="HS25SKL",
        notification_email="suresh.soft09@gmail.com"
    )
    
    print("Store Result:")
    print(result)
    print("-" * 80)
    
    # Parse result
    result_data = json.loads(result)
    
    if result_data.get('success'):
        print("✓ Successfully stored test artifacts!")
        print(f"  - Epics: {result_data['artifact_counts']['epics']}")
        print(f"  - Features: {result_data['artifact_counts']['features']}")
        print(f"  - Use Cases: {result_data['artifact_counts']['use_cases']}")
        print(f"  - Test Cases: {result_data['artifact_counts']['test_cases']}")
    else:
        print("✗ Failed to store artifacts:")
        print(f"  Error: {result_data.get('error')}")
    
    print()
    return result_data.get('success', False)


def test_retrieve_artifacts():
    """Test retrieving test artifacts from DynamoDB"""
    
    print("Testing get_project_artifacts_tool...")
    print("-" * 80)
    
    result = get_project_artifacts_tool(project_id="patient_onboarding_specifications_ada08123")
    
    print("Retrieve Result:")
    print(result)
    print("-" * 80)
    
    # Parse result
    result_data = json.loads(result)
    
    if result_data.get('success'):
        print("✓ Successfully retrieved project artifacts!")
        if 'metadata' in result_data:
            print(f"  Project: {result_data['metadata'].get('project_name', 'N/A')}")
            print(f"  Session: {result_data['metadata'].get('session_id', 'N/A')}")
    else:
        print("✗ Failed to retrieve artifacts:")
        print(f"  Error: {result_data.get('error')}")
    
    print()


if __name__ == "__main__":
    print("=" * 80)
    print("DynamoDB Tools Test Suite")
    print("=" * 80)
    print()
    
    # Test storing artifacts
    success = test_store_artifacts()
    
    # Test retrieving artifacts (only if store was successful)
    if success:
        test_retrieve_artifacts()
    
    print("=" * 80)
    print("Test Complete")
    print("=" * 80)
