#!/usr/bin/env python3

import json
import sys
import os

# Add the misp_stix_converter to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ''))

from misp_stix_converter.stix2misp.external_stix2_to_misp import ExternalSTIX2toMISPParser
from stix2 import parse

def test_oca_conversion():
    print("Testing OCA STIX to MISP conversion...")
    
    # Load the test bundle
    with open('/Users/brianlee/apps/experiments/test-xi-flow/iob-sdo/iobcode/RCTI-main/docs/stix_bundle_global_flow_20250623_152429.json', 'r') as f:
        stix_bundle_dict = json.load(f)
    
    # Parse to STIX2 bundle object (with custom objects allowed)
    stix_bundle = parse(stix_bundle_dict, allow_custom=True)
    
    print(f"Loaded STIX bundle with {len(stix_bundle.objects)} objects")
    
    # Initialize the parser
    parser = ExternalSTIX2toMISPParser()
    
    try:
        # Parse the bundle
        print("Parsing STIX bundle...")
        parser.load_stix_bundle(stix_bundle)
        
        print(f"Loaded {len(stix_bundle.objects)} STIX objects")
        
        parser.parse_stix_bundle()
        
        # Get the MISP event
        misp_event = parser.misp_event
        print(f"Created MISP event: {misp_event.uuid}")
        print(f"Event contains {len(misp_event.objects)} MISP objects")
        print(f"Event contains {len(misp_event.attributes)} MISP attributes")
        
        # Print details of created objects
        for i, obj in enumerate(misp_event.objects):
            print(f"\nObject {i+1}: {obj.name}")
            print(f"  UUID: {obj.uuid}")
            print(f"  Attributes: {len(obj.attributes)}")
            print(f"  References: {len(obj.references) if hasattr(obj, 'references') and obj.references else 0}")
            if hasattr(obj, 'references') and obj.references:
                for ref in obj.references[:2]:  # Show first 2 references
                    print(f"    -> {ref.relationship_type}: {ref.referenced_uuid}")
            for attr in obj.attributes:
                value_str = str(attr.value)
                print(f"    - {attr.object_relation}: {value_str[:50]}{'...' if len(value_str) > 50 else ''}")
        
        # Check for relationships
        if hasattr(parser, '_relationship') and parser._relationship:
            print(f"\nRelationships found: {len(parser._relationship)}")
            for source_uuid, relationships in list(parser._relationship.items())[:3]:  # Show first 3
                print(f"  {source_uuid}: {len(relationships)} relationships")
                for rel in list(relationships)[:2]:  # Show first 2 per source
                    target_ref, rel_type = rel
                    print(f"    -> {rel_type}: {target_ref}")
        else:
            print("\n❌ No relationships found!")
        
        # Print any errors
        if hasattr(parser, '_errors') and parser._errors:
            print(f"\nErrors encountered: {len(parser._errors)}")
            for error in parser._errors:
                print(f"  - {error}")
        else:
            print("\nNo errors encountered!")
            
        return True
        
    except Exception as e:
        print(f"Error during conversion: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_oca_conversion()
    sys.exit(0 if success else 1)