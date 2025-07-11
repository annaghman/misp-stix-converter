#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .stix2converter import ExternalSTIX2Converter
from .stix2mapping import ExternalSTIX2Mapping
from pymisp import MISPObject
from typing import TYPE_CHECKING, Union, Dict

if TYPE_CHECKING:
    from ..external_stix2_to_misp import ExternalSTIX2toMISPParser



class ExternalSTIX2OCAConverter(ExternalSTIX2Converter):

    def __init__(self, main: 'ExternalSTIX2toMISPParser'):
        super().__init__()
        self._set_main_parser(main)
        self._mapping = ExternalSTIX2Mapping

    def parse(self, stix_object_ref: str):
        stix_object = self.main_parser._get_stix_object(stix_object_ref)
        
        # Determine object type and call appropriate method
        object_type = stix_object.get('type') if isinstance(stix_object, dict) else getattr(stix_object, 'type', None)
        
        if object_type == 'x-oca-behavior':
            misp_object = self._create_misp_object_from_oca_behavior(stix_object)
        elif object_type == 'x-oca-detection':
            misp_object = self._create_misp_object_from_oca_detection(stix_object)
        else:
            raise ValueError(f"Unknown OCA object type: {object_type}")
        
        # Create a simple object wrapper if we have a dict
        if isinstance(stix_object, dict):
            class StixObjectWrapper:
                def __init__(self, data):
                    self.id = data['id']
                    self.type = data['type']
                    for key, value in data.items():
                        setattr(self, key, value)
            stix_obj = StixObjectWrapper(stix_object)
        else:
            stix_obj = stix_object
            
        self.main_parser._add_misp_object(misp_object, stix_obj)

    def _create_misp_object_from_oca_behavior(self, stix_object: Union[dict, object]) -> MISPObject:
        misp_object = MISPObject(
            'oca-behavior', 
            force_timestamps=True
        )
        
        # Handle both dict and object types
        if isinstance(stix_object, dict):
            object_id = stix_object.get('id')
            name = stix_object.get('name', '')
            behavior_type = stix_object.get('behavior_type', '')
            created = stix_object.get('created')
            modified = stix_object.get('modified')
        else:
            object_id = getattr(stix_object, 'id', None)
            name = getattr(stix_object, 'name', '')
            behavior_type = getattr(stix_object, 'behavior_type', '')
            created = getattr(stix_object, 'created', None)
            modified = getattr(stix_object, 'modified', None)

        # Set object UUID from STIX ID
        if object_id:
            self.main_parser._sanitise_object_uuid(misp_object, object_id)

        # Set timestamps
        if modified:
            misp_object.timestamp = modified
        if created:
            misp_object.first_seen = created
        if modified:
            misp_object.last_seen = modified

        # Add attributes
        if name:
            misp_object.add_attribute('name', name)

        if behavior_type:
            misp_object.add_attribute('technique-id', behavior_type)
            
            # Parse technique ID to extract main technique and sub-technique
            if '.' in behavior_type:
                main_technique, sub_technique = behavior_type.split('.', 1)
                misp_object.add_attribute('main-technique', main_technique)
                misp_object.add_attribute('sub-technique', sub_technique)
            else:
                misp_object.add_attribute('main-technique', behavior_type)

        if created:
            misp_object.add_attribute('created', created)
        if modified:
            misp_object.add_attribute('modified', modified)
        if object_id:
            misp_object.add_attribute('stix-id', object_id)

        return misp_object

    def _add_object_relationships(self, misp_object: MISPObject):
        """Add relationships from the parser's relationship dictionary to the MISP object."""
        if not hasattr(self.main_parser, '_relationship') or not self.main_parser._relationship:
            return
            
        object_uuid = misp_object.uuid
        if object_uuid in self.main_parser._relationship:
            relationships = self.main_parser._relationship[object_uuid]
            for target_ref, relationship_type in relationships:
                # Convert STIX ID to UUID for MISP reference
                target_uuid = self.main_parser._sanitise_uuid(target_ref)
                misp_object.add_reference(target_uuid, relationship_type)

    def _create_misp_object_from_oca_detection(self, stix_object: Union[dict, object]) -> MISPObject:
        misp_object = MISPObject(
            'oca-detection', 
            force_timestamps=True
        )
        
        # Handle both dict and object types
        if isinstance(stix_object, dict):
            object_id = stix_object.get('id')
            name = stix_object.get('name', '')
            detection_type = stix_object.get('detection_type', '')
            logic = stix_object.get('logic', '')
            created = stix_object.get('created')
            modified = stix_object.get('modified')
        else:
            object_id = getattr(stix_object, 'id', None)
            name = getattr(stix_object, 'name', '')
            detection_type = getattr(stix_object, 'detection_type', '')
            logic = getattr(stix_object, 'logic', '')
            created = getattr(stix_object, 'created', None)
            modified = getattr(stix_object, 'modified', None)

        # Set object UUID from STIX ID
        if object_id:
            self.main_parser._sanitise_object_uuid(misp_object, object_id)

        # Set timestamps
        if modified:
            misp_object.timestamp = modified
        if created:
            misp_object.first_seen = created
        if modified:
            misp_object.last_seen = modified

        # Add attributes
        if name:
            misp_object.add_attribute('name', name)
        if detection_type:
            misp_object.add_attribute('detection-type', detection_type)
        if logic:
            misp_object.add_attribute('detection-logic', logic)
        if created:
            misp_object.add_attribute('created', created)
        if modified:
            misp_object.add_attribute('modified', modified)
        if object_id:
            misp_object.add_attribute('stix-id', object_id)

        return misp_object