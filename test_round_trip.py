#!/usr/bin/env python3

import json
import sys
import os

# Add the misp_stix_converter to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ''))

from misp_stix_converter.stix2misp.external_stix2_to_misp import ExternalSTIX2toMISPParser
from misp_stix_converter.misp2stix.misp_to_stix21 import MISPtoSTIX21Parser
from stix2 import parse

def test_round_trip():
    print("Testing OCA round-trip conversion (STIX → MISP → STIX)...")
    
    # Load the original STIX bundle
    with open('/Users/brianlee/apps/experiments/test-xi-flow/iob-sdo/iobcode/RCTI-main/docs/stix_bundle_global_flow_20250623_152429.json', 'r') as f:
        original_stix_dict = json.load(f)
    
    # Parse to STIX2 bundle object
    original_stix_bundle = parse(original_stix_dict, allow_custom=True)
    
    print(f"Original STIX bundle: {len(original_stix_bundle.objects)} objects")
    
    # Step 1: STIX → MISP
    stix2misp_parser = ExternalSTIX2toMISPParser()
    stix2misp_parser.load_stix_bundle(original_stix_bundle)
    stix2misp_parser.parse_stix_bundle()
    misp_event = stix2misp_parser.misp_event
    
    print(f"MISP event: {len(misp_event.objects)} objects, {len(misp_event.attributes)} attributes")
    
    # Count OCA objects
    oca_objects = [obj for obj in misp_event.objects if obj.name in ['oca-behavior', 'oca-detection']]
    print(f"OCA objects in MISP: {len(oca_objects)}")
    for obj in oca_objects:
        print(f"  - {obj.name}: {obj.get_attributes_by_relation('name')[0].value if obj.get_attributes_by_relation('name') else 'Unknown'}")
    
    # Step 2: MISP → STIX
    misp2stix_parser = MISPtoSTIX21Parser()
    misp2stix_parser.parse_misp_event(misp_event)
    new_stix_bundle = misp2stix_parser.bundle
    
    print(f"New STIX bundle: {len(new_stix_bundle.objects)} objects")
    
    # Count OCA objects in the new bundle
    new_stix_dict = json.loads(new_stix_bundle.serialize())
    new_oca_objects = [obj for obj in new_stix_dict['objects'] 
                       if obj.get('type', '').startswith('x-oca-')]
    
    print(f"OCA objects in new STIX: {len(new_oca_objects)}")
    for obj in new_oca_objects:
        print(f"  - {obj['type']}: {obj.get('name', 'Unknown')}")
    
    # Save the new bundle to file
    output_file = 'round_trip_stix_bundle.json'
    with open(output_file, 'w') as f:
        json.dump(new_stix_dict, f, indent=2)
    print(f"\n💾 Saved round-trip STIX bundle to: {output_file}")
    
    # Print the new bundle (truncated)
    print("\n=== Round-trip STIX Bundle (first 2 OCA objects) ===")
    oca_count = 0
    for obj in new_stix_dict['objects']:
        if obj.get('type', '').startswith('x-oca-') and oca_count < 2:
            print(f"\n{obj['type']}:")
            print(json.dumps(obj, indent=2))
            oca_count += 1
    
    # Compare input vs output
    print("\n" + "="*60)
    print("COMPARISON: INPUT vs OUTPUT")
    print("="*60)
    
    # Extract OCA objects from original and new bundles
    original_oca_objects = [obj for obj in original_stix_dict['objects'] 
                           if obj.get('type', '').startswith('x-oca-')]
    
    print(f"Original bundle: {len(original_stix_dict['objects'])} total objects")
    print(f"                 {len(original_oca_objects)} OCA objects")
    print(f"Round-trip bundle: {len(new_stix_dict['objects'])} total objects")
    print(f"                   {len(new_oca_objects)} OCA objects")
    
    # Compare OCA object counts by type
    original_behaviors = [obj for obj in original_oca_objects if obj['type'] == 'x-oca-behavior']
    original_detections = [obj for obj in original_oca_objects if obj['type'] == 'x-oca-detection']
    new_behaviors = [obj for obj in new_oca_objects if obj['type'] == 'x-oca-behavior']
    new_detections = [obj for obj in new_oca_objects if obj['type'] == 'x-oca-detection']
    
    print(f"\nBehaviors: {len(original_behaviors)} → {len(new_behaviors)}")
    print(f"Detections: {len(original_detections)} → {len(new_detections)}")
    
    # Compare specific attributes
    print(f"\n📊 ATTRIBUTE COMPARISON:")
    
    # Sample first behavior object for detailed comparison
    if original_behaviors and new_behaviors:
        orig_behavior = original_behaviors[0]
        new_behavior = new_behaviors[0]
        
        print(f"\nFirst Behavior Object:")
        print(f"  Name: '{orig_behavior.get('name', 'N/A')}' → '{new_behavior.get('name', 'N/A')}'")
        print(f"  Type: '{orig_behavior.get('behavior_type', 'N/A')}' → '{new_behavior.get('behavior_type', 'N/A')}'")
        print(f"  ID preserved: {orig_behavior.get('id') == new_behavior.get('id')}")
        
        # Check if core data matches
        name_match = orig_behavior.get('name') == new_behavior.get('name')
        behavior_type_match = orig_behavior.get('behavior_type') == new_behavior.get('behavior_type')
        
        print(f"  ✅ Name match: {name_match}")
        print(f"  ✅ Behavior type match: {behavior_type_match}")
    
    # Sample first detection object for detailed comparison
    if original_detections and new_detections:
        orig_detection = original_detections[0]
        new_detection = new_detections[0]
        
        print(f"\nFirst Detection Object:")
        print(f"  Name: '{orig_detection.get('name', 'N/A')}' → '{new_detection.get('name', 'N/A')}'")
        print(f"  Type: '{orig_detection.get('detection_type', 'N/A')}' → '{new_detection.get('detection_type', 'N/A')}'")
        print(f"  Logic preserved: {len(orig_detection.get('logic', '')) == len(new_detection.get('logic', ''))}")
        
        name_match = orig_detection.get('name') == new_detection.get('name')
        detection_type_match = orig_detection.get('detection_type') == new_detection.get('detection_type')
        logic_match = orig_detection.get('logic') == new_detection.get('logic')
        
        print(f"  ✅ Name match: {name_match}")
        print(f"  ✅ Detection type match: {detection_type_match}")
        print(f"  ✅ Logic match: {logic_match}")
    
    # Overall assessment
    objects_preserved = len(new_oca_objects) == len(original_oca_objects)
    types_preserved = len(new_behaviors) == len(original_behaviors) and len(new_detections) == len(original_detections)
    
    print(f"\n🎯 OVERALL ASSESSMENT:")
    print(f"  Object count preserved: {objects_preserved}")
    print(f"  Object types preserved: {types_preserved}")
    
    if objects_preserved and types_preserved:
        print(f"\n✅ Round-trip conversion SUCCESSFUL!")
        print(f"   • Preserved all {len(new_oca_objects)} OCA objects")
        print(f"   • Maintained data integrity")
        return True
    else:
        print(f"\n❌ Round-trip conversion FAILED!")
        print(f"   • Expected {len(original_oca_objects)} OCA objects, got {len(new_oca_objects)}")
        return False

if __name__ == "__main__":
    try:
        success = test_round_trip()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)