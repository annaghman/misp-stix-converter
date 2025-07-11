# OCA (Open Cybersecurity Alliance) Extension Implementation

This document details the implementation of Open Cybersecurity Alliance (OCA) custom object support for the MISP-STIX-Converter library, enabling bidirectional conversion of `x-oca-behavior` and `x-oca-detection` objects between MISP and STIX 2.1 formats.

Refer also to [MISP-STIX-Readme.md] (https://github.com/annaghman/misp-stix-converter/blob/main/MISP-STIX-Readme.md) for background knowledge

## Implementation Overview

The OCA extension adds support for two custom STIX object types:
- **`x-oca-behavior`** - Represents cybersecurity behaviors and techniques (often MITRE ATT&CK techniques)
- **`x-oca-detection`** - Represents detection rules and logic for identifying behaviors

### Key Features Implemented

✅ **Bidirectional Conversion**: Full STIX ↔ MISP ↔ STIX round-trip conversion  
✅ **Relationship Preservation**: Maintains connections between behaviors and detections  
✅ **MITRE ATT&CK Integration**: Proper handling of technique IDs and external references  
✅ **Data Integrity**: Preserves object names, types, detection logic, and metadata  
✅ **Standards Compliance**: Follows STIX 2.1 custom object specifications  

## Architecture and Design Approach

### Phase 1: STIX → MISP Conversion

The implementation follows the existing converter pattern used by other STIX object types:

1. **Object Registration**: OCA objects are registered in the converter mapping system
2. **Custom Converter**: A dedicated `ExternalSTIX2OCAConverter` handles OCA-specific conversion logic
3. **MISP Object Creation**: STIX objects are converted to corresponding MISP objects with proper attributes
4. **Relationship Handling**: STIX relationships are converted to MISP ObjectReferences

### Phase 2: MISP → STIX Conversion

The reverse conversion integrates with the existing MISP-to-STIX pipeline:

1. **Object Mapping**: MISP OCA objects are mapped to custom parser methods
2. **Custom Parsers**: Dedicated parsing methods handle conversion to STIX format
3. **Custom Object Definitions**: STIX 2.1 CustomObject decorators define the object schemas
4. **Relationship Recreation**: MISP ObjectReferences are converted back to STIX relationship objects

## Files Modified and Changes Made

### 1. **misp_stix_converter/__init__.py**
**Purpose**: Package initialization and feature loading  
**Changes Made**:
- Added OCA object support to the `_LOADED_FEATURES` dictionary
- Registered `'oca-behavior'` and `'oca-detection'` as supported object types
- This ensures OCA objects are recognized throughout the conversion pipeline

### 2. **misp_stix_converter/stix2misp/external_stix2_mapping.py**
**Purpose**: Mapping configuration for external STIX to MISP conversion  
**Changes Made**:
- Added object type mappings for OCA custom objects:
  - `'x-oca-behavior': 'oca-behavior'`
  - `'x-oca-detection': 'oca-detection'`
- This routes incoming STIX OCA objects to the appropriate MISP object types

### 3. **misp_stix_converter/stix2misp/external_stix2_to_misp.py**
**Purpose**: Main parser for external STIX bundles to MISP events  
**Changes Made**:
- Added `'oca-behavior'` and `'oca-detection'` to the `_OBJECT_CONVERTERS` mapping
- Both object types are routed to the `ExternalSTIX2OCAConverter` class
- This ensures OCA objects are processed by the correct converter during parsing

### 4. **misp_stix_converter/stix2misp/converters/stix2_oca_converter.py** *(NEW FILE)*
**Purpose**: Custom converter for OCA objects  
**Implementation Details**:
- **`ExternalSTIX2OCAConverter`** class inheriting from `ExternalSTIX2Converter`
- **Object Type Detection**: Automatically determines whether to handle behavior or detection objects
- **MISP Object Creation**:
  - Creates MISP `oca-behavior` objects with attributes: `name`, `technique-id`, `main-technique`, `sub-technique`, `created`, `modified`, `stix-id`
  - Creates MISP `oca-detection` objects with attributes: `name`, `detection-type`, `detection-logic`, `created`, `modified`, `stix-id`
- **Technique ID Parsing**: Automatically splits compound technique IDs (e.g., "T1078.001" → main: "T1078", sub: "001")
- **Timestamp Handling**: Preserves STIX timestamps in MISP objects
- **UUID Management**: Maintains object UUID consistency between STIX and MISP formats

### 5. **misp_stix_converter/misp2stix/stix21_mapping.py**
**Purpose**: Object mapping and routing for MISP to STIX 2.1 conversion  
**Changes Made**:
- Added entries to `__objects_mapping` dictionary:
  - `'oca-behavior': '_parse_oca_behavior_object'`
  - `'oca-detection': '_parse_oca_detection_object'`
- This routes MISP OCA objects to custom parsing methods during STIX conversion

### 6. **misp_stix_converter/misp2stix/misp_to_stix21.py**
**Purpose**: Main converter for MISP to STIX 2.1 format  
**Changes Made**:

#### Custom Object Definitions
- **`OCABehavior`** CustomObject decorator with schema:
  - `id`, `labels`, `created`, `modified`, `created_by_ref` (standard STIX fields)
  - `name`, `behavior_type`, `external_references` (OCA-specific fields)
- **`OCADetection`** CustomObject decorator with schema:
  - `id`, `labels`, `created`, `modified`, `created_by_ref` (standard STIX fields)  
  - `name`, `detection_type`, `logic` (OCA-specific fields)

#### Custom Parsing Methods
- **`_parse_oca_behavior_object()`**:
  - Extracts MISP attributes (`name`, `technique-id`, etc.)
  - Creates STIX `x-oca-behavior` object
  - Generates MITRE ATT&CK external references with proper URLs
  - Handles relationship conversion via `_parse_object_relationships()`
- **`_parse_oca_detection_object()`**:
  - Extracts MISP attributes (`name`, `detection-type`, `detection-logic`)
  - Creates STIX `x-oca-detection` object
  - Preserves complex detection logic and rules
  - Handles relationship conversion via `_parse_object_relationships()`

#### External Reference Generation
- Automatically creates MITRE ATT&CK external references using technique IDs
- Generates proper URLs: `https://attack.mitre.org/techniques/{technique_id}/`
- Preserves both main techniques (T1078) and sub-techniques (T1078.001)

#### Relationship Handling
- Integrates with existing `_parse_object_relationships()` method
- Converts MISP ObjectReferences to STIX relationship objects
- Maintains relationship types (`uses`, `occurs-before`, etc.)
- Preserves relationship timestamps and metadata

## Technical Implementation Details

### Custom Object Schema Design

The STIX 2.1 custom objects follow standard conventions while incorporating OCA-specific fields:

```python
@CustomObject(
    'x-oca-behavior',
    [
        ('id', IDProperty('x-oca-behavior', spec_version='2.1')),
        ('labels', ListProperty(StringProperty, required=True)),
        ('created', TimestampProperty(required=True, precision='millisecond')),
        ('modified', TimestampProperty(required=True, precision='millisecond')),
        ('created_by_ref', ReferenceProperty(valid_types='identity', spec_version='2.1')),
        ('name', StringProperty(required=True)),
        ('behavior_type', StringProperty(required=True)),
        ('external_references', ListProperty(DictionaryProperty))
    ]
)
```

### Attribute Mapping Strategy

**STIX to MISP Mapping**:
- `name` → MISP attribute `name`
- `behavior_type` → MISP attribute `technique-id`
- `detection_type` → MISP attribute `detection-type`
- `logic` → MISP attribute `detection-logic`
- STIX timestamps → MISP object timestamps
- STIX ID → MISP attribute `stix-id`

**MISP to STIX Mapping**:
- MISP attribute `name` → STIX `name`
- MISP attribute `technique-id` → STIX `behavior_type`
- MISP attribute `detection-type` → STIX `detection_type`
- MISP attribute `detection-logic` → STIX `logic`
- MISP timestamps → STIX timestamps
- Auto-generated external references for ATT&CK techniques

### Relationship Preservation

The implementation leverages the existing relationship handling infrastructure:

1. **STIX → MISP**: STIX relationships are processed by the main parser and stored in the `_relationship` dictionary, then converted to MISP ObjectReferences
2. **MISP → STIX**: MISP ObjectReferences are processed by `_parse_object_relationships()` to recreate STIX relationship objects
3. **Relationship Types**: Preserves standard relationship types like `uses`, `occurs-before`, `detects`, etc.
4. **UUID Consistency**: Maintains consistent object identification across conversions

### Error Handling and Validation

- **Type Validation**: Validates object types before processing
- **Attribute Extraction**: Safely handles missing or malformed attributes
- **Timestamp Conversion**: Robust handling of different timestamp formats
- **UUID Sanitization**: Ensures proper UUID format conversion between STIX and MISP

## Testing and Validation

The implementation includes comprehensive testing:

### Test Files Created
- **`test_oca_implementation.py`**: STIX → MISP conversion testing
- **`test_round_trip.py`**: End-to-end STIX → MISP → STIX validation
- **Sample data files**: Real-world OCA objects for testing

### Validation Criteria
- **Object Count Preservation**: All input objects present in output
- **Attribute Accuracy**: Names, types, and logic preserved exactly
- **Relationship Integrity**: All relationships maintained with correct types
- **STIX Compliance**: Output validates against STIX 2.1 specification
- **Round-trip Fidelity**: Input ≈ Output (accounting for format differences)

### STIX Visualizer Testing
The final validation used external STIX visualization tools to confirm:
- Objects render correctly as nodes
- Relationships display as proper connections
- Object types are recognized
- No structural errors or invalid references

## Usage Examples

### Converting STIX Bundle with OCA Objects to MISP

```python
from misp_stix_converter.stix2misp.external_stix2_to_misp import ExternalSTIX2toMISPParser
from stix2 import parse

# Load STIX bundle containing OCA objects
with open('oca_bundle.json', 'r') as f:
    stix_bundle_dict = json.load(f)

stix_bundle = parse(stix_bundle_dict, allow_custom=True)

# Convert to MISP
parser = ExternalSTIX2toMISPParser()
parser.load_stix_bundle(stix_bundle)
parser.parse_stix_bundle()

misp_event = parser.misp_event
```

### Converting MISP Event with OCA Objects to STIX

```python
from misp_stix_converter.misp2stix.misp_to_stix21 import MISPtoSTIX21Parser

# Convert MISP event containing OCA objects
parser = MISPtoSTIX21Parser()
parser.parse_misp_event(misp_event)

stix_bundle = parser.bundle
```

## Future Enhancements

### Potential Extensions
- **Additional OCA Object Types**: Support for other OCA specifications as they emerge
- **Enhanced Metadata**: Preserve additional STIX metadata fields
- **Validation Rules**: Built-in validation for OCA object schemas
- **Performance Optimization**: Caching and batch processing improvements

### Compatibility Considerations
- **STIX Version Support**: Currently targets STIX 2.1; could be extended to STIX 2.0
- **MISP Version Compatibility**: Designed to work with current MISP object templates
- **Custom Extensions**: Architecture supports additional custom object types

## Integration with Existing Codebase

The OCA implementation seamlessly integrates with the existing MISP-STIX-Converter architecture:

- **No Breaking Changes**: Existing functionality remains unaffected
- **Consistent Patterns**: Follows established converter and mapping patterns
- **Extensible Design**: Other custom object types can be added using the same approach
- **Backward Compatibility**: Standard MISP and STIX objects continue to work as before

This implementation provides a robust foundation for OCA object support while maintaining the library's existing capabilities and design principles.
