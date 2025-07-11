# Installation Guide - OCA Extension for MISP-STIX-Converter

This guide provides step-by-step instructions for deploying the OCA (Open Cybersecurity Alliance) extension to a MISP instance in production.

## Prerequisites

### System Requirements
- **MISP Instance**: Running MISP version 2.4.140+ (recommended)
- **Python**: Version 3.9 or higher
- **Administrative Access**: Root or sudo access to the MISP server
- **Backup**: Current backup of your MISP instance and database

### Required Dependencies
- PyMISP
- STIX2 Python library
- Python virtual environment (recommended)

## Pre-Installation Steps

### 1. Create System Backup
```bash
# Backup MISP database
sudo mysqldump misp > misp_backup_$(date +%Y%m%d).sql

# Backup MISP application directory
sudo tar -czf misp_app_backup_$(date +%Y%m%d).tar.gz /var/www/MISP/

# Backup current Python packages
pip freeze > misp_packages_backup.txt
```

### 2. Identify MISP Installation Details
```bash
# Find MISP installation directory
ls -la /var/www/MISP/

# Check current misp-stix version
cd /var/www/MISP/
source venv/bin/activate  # If using virtual environment
pip show misp-stix
```

### 3. Verify Current STIX Functionality
```bash
# Test existing STIX conversion in MISP web interface
# Go to: Events → Export → STIX (any format)
# Ensure this works before proceeding
```

## Installation Methods

### Method 1: Direct Replacement (Recommended for Production)

#### Step 1: Stop MISP Services
```bash
sudo systemctl stop apache2
sudo systemctl stop misp-workers
sudo systemctl stop misp-scheduler
```

#### Step 2: Activate MISP Environment
```bash
cd /var/www/MISP/
source venv/bin/activate  # If using virtual environment
```

#### Step 3: Backup Current Installation
```bash
pip show misp-stix | grep Location
# Note the location, then backup
cp -r /path/to/misp-stix /path/to/misp-stix-backup
```

#### Step 4: Install OCA Extension
```bash
# Option A: Install from local directory
pip uninstall misp-stix -y
pip install /path/to/your/MISP-STIX-Converter/

# Option B: Install from package
pip uninstall misp-stix -y
pip install /path/to/your/MISP-STIX-Converter/dist/misp_stix_converter-*.whl
```

#### Step 5: Verify Installation
```bash
python -c "
from misp_stix_converter import __version__
print(f'MISP-STIX Version: {__version__}')

from misp_stix_converter.stix2misp.converters.stix2_oca_converter import ExternalSTIX2OCAConverter
print('OCA converter loaded successfully')

from misp_stix_converter.misp2stix.misp_to_stix21 import MISPtoSTIX21Parser
print('OCA STIX export capability loaded')
"
```

#### Step 6: Start MISP Services
```bash
sudo systemctl start misp-workers
sudo systemctl start misp-scheduler
sudo systemctl start apache2
```

### Method 2: Development Installation (For Testing)

#### Step 1: Install in Development Mode
```bash
cd /var/www/MISP/
source venv/bin/activate
pip install -e /path/to/your/MISP-STIX-Converter/
```

This allows you to make changes without reinstalling.

### Method 3: Package-Based Installation

#### Step 1: Create Distribution Package
```bash
cd /path/to/your/MISP-STIX-Converter/
python setup.py sdist bdist_wheel
```

#### Step 2: Install Package
```bash
cd /var/www/MISP/
source venv/bin/activate
pip install /path/to/your/MISP-STIX-Converter/dist/misp_stix_converter-*.whl
```

## MISP Object Template Configuration

### 1. Verify Object Templates Exist

#### Check via Web Interface:
1. Navigate to: **Administration → Object Templates**
2. Search for: `oca-behavior` and `oca-detection`
3. If not present, proceed to create them

#### Check via Command Line:
```bash
# Connect to MISP database
mysql -u misp -p misp

# Check for OCA object templates
SELECT * FROM object_templates WHERE name IN ('oca-behavior', 'oca-detection');
```

### 2. Create Missing Object Templates (If Needed)

If the templates don't exist, create them in MISP:

#### Option A: Via Web Interface
1. Go to: **Administration → Object Templates → Add Object Template**
2. Create templates with the following specifications:

**oca-behavior template:**
- **Name**: `oca-behavior`
- **Meta-category**: `threat-analysis`
- **Description**: `OCA behavior object representing cybersecurity techniques`
- **Attributes**:
  - `name` (text, required)
  - `technique-id` (text, required)
  - `main-technique` (text)
  - `sub-technique` (text)
  - `created` (datetime)
  - `modified` (datetime)
  - `stix-id` (text)

**oca-detection template:**
- **Name**: `oca-detection`
- **Meta-category**: `threat-analysis`
- **Description**: `OCA detection object representing detection rules`
- **Attributes**:
  - `name` (text, required)
  - `detection-type` (text, required)
  - `detection-logic` (text, required)
  - `created` (datetime)
  - `modified` (datetime)
  - `stix-id` (text)

#### Option B: Import from JSON
```bash
# If you have object template JSON files
curl -X POST -H "Authorization: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d @oca-behavior-template.json \
     https://your-misp-instance/object_templates/add

curl -X POST -H "Authorization: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d @oca-detection-template.json \
     https://your-misp-instance/object_templates/add
```

## Testing and Validation

### 1. Test STIX Import with OCA Objects

#### Prepare Test Data:
```bash
# Use the provided test file
cp /path/to/your/MISP-STIX-Converter/round_trip_stix_bundle_viz_round.json /tmp/test_oca.json
```

#### Import via Web Interface:
1. Go to: **Events → Import from STIX**
2. Upload: `/tmp/test_oca.json`
3. Verify: OCA objects are created as `oca-behavior` and `oca-detection` MISP objects
4. Check: Relationships between objects are preserved

#### Import via API:
```bash
curl -X POST -H "Authorization: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -F "file=@/tmp/test_oca.json" \
     https://your-misp-instance/events/import_stix
```

### 2. Test STIX Export with OCA Objects

#### Via Web Interface:
1. Navigate to the event created above
2. Go to: **Export → STIX 2.1**
3. Verify: Downloaded file contains `x-oca-behavior` and `x-oca-detection` objects
4. Check: External references point to correct MITRE ATT&CK URLs

#### Via API:
```bash
curl -H "Authorization: YOUR_API_KEY" \
     https://your-misp-instance/events/restSearch/stix2/eventid:EVENT_ID
```

### 3. Validate Round-Trip Conversion

#### Test Full Cycle:
1. **Import**: STIX bundle with OCA objects → MISP event
2. **Export**: MISP event → STIX bundle
3. **Compare**: Original vs. final STIX bundle for object preservation

#### Expected Results:
- ✅ All OCA objects preserved
- ✅ Relationships maintained
- ✅ MITRE ATT&CK external references intact
- ✅ Object names and types preserved
- ✅ Detection logic preserved

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Import Errors
**Symptoms**: STIX import fails with unknown object type errors
**Solution**: 
```bash
# Check if OCA objects are registered
python -c "
from misp_stix_converter import _LOADED_FEATURES
print('OCA objects supported:', 'oca-behavior' in _LOADED_FEATURES)
"
```

#### Issue 2: Missing Object Templates
**Symptoms**: OCA objects not created during import
**Solution**: Create object templates as described above

#### Issue 3: Export Errors
**Symptoms**: STIX export fails or missing OCA objects
**Solution**:
```bash
# Verify export mappings
python -c "
from misp_stix_converter.misp2stix.stix21_mapping import MISPtoSTIX21Mapping
print('OCA mappings:', MISPtoSTIX21Mapping.objects_mapping('oca-behavior'))
"
```

#### Issue 4: Relationship Issues
**Symptoms**: OCA objects imported but relationships missing
**Solution**: Check MISP logs for relationship parsing errors:
```bash
sudo tail -f /var/www/MISP/app/tmp/logs/error.log
```

### Log File Locations
- **MISP Application Logs**: `/var/www/MISP/app/tmp/logs/`
- **Apache Logs**: `/var/log/apache2/`
- **System Logs**: `/var/log/syslog`

### Diagnostic Commands
```bash
# Check Python import paths
python -c "import sys; print('\n'.join(sys.path))"

# Verify MISP-STIX installation
pip list | grep misp-stix

# Test database connectivity
mysql -u misp -p misp -e "SELECT COUNT(*) FROM object_templates;"
```

## Rollback Procedure

### If Issues Occur:

#### 1. Stop Services
```bash
sudo systemctl stop apache2 misp-workers misp-scheduler
```

#### 2. Restore Previous Version
```bash
cd /var/www/MISP/
source venv/bin/activate
pip uninstall misp-stix -y
pip install misp-stix  # Installs latest official version
# OR restore from backup
cp -r /path/to/misp-stix-backup/* /path/to/misp-stix-location/
```

#### 3. Restore Database (If Needed)
```bash
mysql -u root -p misp < misp_backup_YYYYMMDD.sql
```

#### 4. Restart Services
```bash
sudo systemctl start misp-workers misp-scheduler apache2
```

## Post-Installation Configuration

### 1. Update MISP Settings
- **Administration → Server Settings → STIX**
- Ensure STIX 2.1 export is enabled
- Configure default sharing levels as needed

### 2. User Training
- Inform users about new OCA object types
- Provide documentation on MITRE ATT&CK technique format
- Train on relationship creation between behaviors and detections

### 3. Monitoring
- Monitor MISP logs for import/export errors
- Set up alerts for failed STIX conversions
- Regular testing of OCA object functionality

## Support and Maintenance

### Regular Maintenance Tasks
- **Weekly**: Test OCA import/export functionality
- **Monthly**: Review logs for errors or performance issues
- **Quarterly**: Validate against latest MITRE ATT&CK framework updates

### Getting Help
- Check logs first: `/var/www/MISP/app/tmp/logs/`
- Review this documentation
- Test with provided sample files
- Consult OCA_IMPLEMENTATION.md for technical details

### Updates and Patches
When updating the OCA extension:
1. Follow the same installation procedure
2. Test thoroughly in staging environment first
3. Maintain backups of working versions

This completes the installation guide for the OCA extension. The extension should now be fully functional in your MISP instance.