#!/usr/bin/env python3

# Copyright (c) 2024 Memorial Sloan-Kettering Cancer Center.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY, WITHOUT EVEN THE IMPLIED WARRANTY OF
# MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.  The software and
# documentation provided hereunder is on an "as is" basis, and
# Memorial Sloan-Kettering Cancer Center
# has no obligations to provide maintenance, support,
# updates, enhancements or modifications.  In no event shall
# Memorial Sloan-Kettering Cancer Center
# be liable to any party for direct, indirect, special,
# incidental or consequential damages, including lost profits, arising
# out of the use of this software and its documentation, even if
# Memorial Sloan-Kettering Cancer Center
# has been advised of the possibility of such damage.

# TODO modified file will have extra column at end which will take onctoree codes as parent - require that 2 parent columns before it have been deleted, then I can generate UUID URIs and get the label
# TODO maybe only show changes to precursors/revocations? instead of the whole history
# TODO what to do about deletes? Maybe discuss with Rob? -- for now tell them to manually delete them

import argparse
from collections import defaultdict
import csv
from deepdiff import DeepDiff
import os
import requests
import sys

GITHUB_RESOURCE_URI_TO_ONCOCODE_MAPPING_FILE_URL = "https://raw.githubusercontent.com/cBioPortal/oncotree/refs/heads/master/resources/resource_uri_to_oncocode_mapping.txt"
HELP_FOR_FILE_FORMAT = "In the Graphite 'Concept Manager' left sidebar 'Hierarchy' tab, select your oncotree version, then click on the 'Export' tab in the main panel.  For 'File Format' select 'CSV (Dynamic Property Columns)'. In the 'Include' section uncheck everything except 'Non-primary concept URI' and 'Status'.  In the 'Select Properties to Export' all fields in both 'OncoTree Tumor Type' and 'SKOS' should be selected."
LABEL = "Primary Concept"
RESOURCE_URI = "Resource URI"
ONCOTREE_CODE = "notation (SKOS)"
SCHEME_URI = "skos:inScheme URI"
STATUS = "Status"
INTERNAL_ID = "clinicalCasesSubset (OncoTree Tumor Type)"
COLOR = "color (OncoTree Tumor Type)"
MAIN_TYPE = "mainType (OncoTree Tumor Type)"
PRECURSORS = "precursors (OncoTree Tumor Type)"
PREFERRED_LABEL = "preferred label (SKOS)"
REVOCATIONS = "revocations (OncoTree Tumor Type)"
PARENT_RESOURCE_URI = "has broader (SKOS) URI"
PARENT_LABEL = "has broader (SKOS)"
PARENT_ONCOTREE_CODE = "parent oncotree code"
EXPECTED_HEADER = [RESOURCE_URI, LABEL, SCHEME_URI, STATUS, INTERNAL_ID, COLOR, MAIN_TYPE, ONCOTREE_CODE, PRECURSORS, PREFERRED_LABEL, REVOCATIONS, PARENT_RESOURCE_URI, PARENT_LABEL]
EXPECTED_HEADER_MODIFIED_FILE = EXPECTED_HEADER + [PARENT_ONCOTREE_CODE]
REQUIRED_FIELDS = [LABEL, SCHEME_URI, STATUS, INTERNAL_ID, COLOR, MAIN_TYPE, ONCOTREE_CODE, PREFERRED_LABEL, PARENT_RESOURCE_URI, PARENT_LABEL]
TISSUE_NODE_REQUIRED_FIELDS = [RESOURCE_URI, LABEL, SCHEME_URI, STATUS, INTERNAL_ID, ONCOTREE_CODE, PREFERRED_LABEL]

def confirm_change(message):
    print(f"\n{message}")
    answer = input("Enter [y]es if the changes were intentional, [n]o if not: ")
    if answer.lower() in ["y","yes"]:
        return True 
    return False

def construct_pretty_label_for_row(internal_id, code, label):
    return f"{internal_id}: {label} ({code})"

# C01 + C02 + C03 -> C04
# C01, C02, and C03 become precursors to C04
# C05 -> C06 + C07 + C08
# C05 is a precursor to C06, C07, and C08
# you can have one concept be a precursor to many concepts
def get_all_precursors(csv_file):
    with open(csv_file, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        precursor_id_to_internal_ids = defaultdict(set)
        for row in reader:
            if row[PRECURSORS]:
                for precursor_id in row[PRECURSORS].split(): # space separated
                    precursor_id_to_internal_ids[precursor_id].add(row[INTERNAL_ID])
        return precursor_id_to_internal_ids

# C01 + C02 + C03 -> C01
# C02 and CO3 become revocations in C01
# don't revoke anything with precursors (according to Rob's document "Oncotree History Modeling") - check that anything in revocations is not a precursor
# a concept can only be revoked by a pre-existing concept
def get_all_revocations(csv_file):
    with open(csv_file, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        revocation_id_to_internal_ids = defaultdict(set)
        for row in reader:
            if row[REVOCATIONS]:
                for revocation_id in row[REVOCATIONS].split(): # space separated
                    revocation_id_to_internal_ids[revocation_id].add(row[INTERNAL_ID])
        return revocation_id_to_internal_ids   

def get_resource_uri_to_internal_ids(csv_file):
    with open(csv_file, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        resource_uri_to_internal_ids = {}
        for row in reader:
            resource_uri_to_internal_ids[row[RESOURCE_URI]] = row[INTERNAL_ID]
        return resource_uri_to_internal_ids

def get_oncotree_codes_to_internal_ids(csv_file):
    with open(csv_file, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        oncotree_codes_to_internal_ids = {}
        for row in reader:
            oncotree_codes_to_internal_ids[row[ONCOTREE_CODE]] = row[INTERNAL_ID]
        return oncotree_codes_to_internal_ids

def get_parent_internal_id(child_internal_id, parent_resource_uri, parent_oncotree_code, oncotree_codes_to_internal_ids, resource_uri_to_internal_ids):
    if parent_oncotree_code:
        # TODO validate parent_oncotree_codes in validate method?
        if parent_oncotree_code in oncotree_codes_to_internal_ids:    
            return oncotree_codes_to_internal_ids[parent_oncotree_code]
        else:
            print(f"Error: '{PARENT_ONCOTREE_CODE}' '{parent_oncotree_code}' not found in modified file", file=sys.stderr)
            sys.exit(1)
    if not parent_resource_uri:
        print(f"Error: either '{PARENT_ONCOTREE_CODE}' or '{PARENT_RESOURCE_URI}' are required in the modified file, missing for '{child_internal_id}'", file=sys.stderr) 
        sys.exit(1)
    # we must have the parent_resource_uri instead
    return resource_uri_to_internal_ids[parent_resource_uri]
        
def get_oncotree_code_from_internal_id(oncotree_codes_to_internal_ids, internal_id):
    for code in oncotree_codes_to_internal_ids:
        if oncotree_codes_to_internal_ids[code] == internal_id:
            return code
    print(f"Error: could not find an oncotree code for internal id {internal_id}", file=sys.stderr)
    sys.exit(1)

def confirm_changes(original_oncotree,
                    modified_oncotree,
                    precursor_id_to_internal_ids,
                    revocation_id_to_internal_ids,
                    original_resource_uri_to_internal_ids,
                    modified_resource_uri_to_internal_ids,
                    internal_id_to_oncocodes,
                    oncotree_codes_to_internal_ids):
    original_internal_id_set = set(original_oncotree.keys())
    modified_internal_id_set = set(modified_oncotree.keys())

    # get three sets of INTERNAL_IDs:
    # 1) ones that have been removed
    # 2) ones that are new
    # 3) ones that are still there
    # then handle each of the three sets
    removed_internal_ids = original_internal_id_set - modified_internal_id_set
    new_internal_ids = modified_internal_id_set - original_internal_id_set
    in_both_internal_ids = original_internal_id_set & modified_internal_id_set

    #print(removed_internal_ids)
    #print(new_internal_ids)
    #print(in_both_internal_ids)

    all_changes_are_intentional = True

    print("\nRemoved internal ids:")
    if removed_internal_ids:
        for internal_id in sorted(removed_internal_ids):
            data = original_oncotree[internal_id]
            pretty_label = construct_pretty_label_for_row(data[INTERNAL_ID], data[ONCOTREE_CODE], data[LABEL])
            print(f"\t{pretty_label}")
        print(f"\n****** All removed Oncotree nodes must be manually deleted from Graphite")
    else:
        print("\tNone")

    print("\nNew internal ids:")
    if new_internal_ids:
        for internal_id in sorted(new_internal_ids):
            data = modified_oncotree[internal_id]
            pretty_label = construct_pretty_label_for_row(data[INTERNAL_ID], data[ONCOTREE_CODE], data[LABEL])
            if data[RESOURCE_URI]:
                # we could allow this but we would have to make sure the resource uri is new and is valid - so let's not
                print(f"Error: you cannot have a '{RESOURCE_URI}' for a new oncotree node '{pretty_label}'", file=sys.stderr) 
                sys.exit(1)
            # show parent in "new" nodes
            parent_internal_id = get_parent_internal_id(internal_id, data[PARENT_RESOURCE_URI], data[PARENT_ONCOTREE_CODE], oncotree_codes_to_internal_ids, modified_resource_uri_to_internal_ids)
            parent_data = modified_oncotree[parent_internal_id]
            parent_pretty_label = construct_pretty_label_for_row(parent_internal_id, parent_data[ONCOTREE_CODE], parent_data[LABEL])
            print(f"\t{pretty_label} has parent {parent_pretty_label}")
    else:
        print("\tNone")

    print("\nPrecurors:")
    if precursor_id_to_internal_ids:
        for precursor_id in sorted(precursor_id_to_internal_ids.keys()):
            precursor_code = internal_id_to_oncocodes[precursor_id] if precursor_id in internal_id_to_oncocodes else "unknown"
            # are any current concepts precursors? they shouldn't be
            if precursor_id in modified_internal_id_set:
                print(f"Error: '{precursor_id}' ('{precursor_code}') is a precuror to '{','.join(precursor_id_to_internal_ids[precursor_id])}' but '{precursor_id}' is still in this file as a current record", file=sys.stderr)
                sys.exit(1)
            precursor_of_set = precursor_id_to_internal_ids[precursor_id]
            for internal_id in precursor_of_set:
                data = modified_oncotree[internal_id]
                pretty_label = construct_pretty_label_for_row(data[INTERNAL_ID], data[ONCOTREE_CODE], data[LABEL])
                print(f"\t'{precursor_id}' ('{precursor_code}') -> '{pretty_label}'")
    else:
        print("\tNone")

    print("\nRevocations:")
    if revocation_id_to_internal_ids: 
        for revocation_id in sorted(revocation_id_to_internal_ids.keys()):
            revocation_code = internal_id_to_oncocodes[revocation_id] if revocation_id in internal_id_to_oncocodes else "unknown"
            if revocation_id in modified_internal_id_set:
                print(f"Error: '{revocation_id}' ('{revocation_code}') has been revoked by '{','.join(revocation_id_to_internal_ids[revocation_id])}' but '{revocation_id}' is still in this file as a current record", file=sys.stderr)
                sys.exit(1)
            if revocation_id in precursor_id_to_internal_ids:
                print(f"Error: Revocation '{revocation_id}' ('{revocation_code}') cannot also be a precursor", file=sys.stderr)
                sys.exit(1)
            revocation_of_set = revocation_id_to_internal_ids[revocation_id]
            for internal_id in revocation_of_set: 
                if internal_id in new_internal_ids:
                    print(f"Error: '{revocation_id}' ('{revocation_code}') revokes '{internal_id}' but '{internal_id}' is a new concept. Only a pre-existing concept can revoke something", file=sys.stderr)
                    sys.exit(1)
                data = modified_oncotree[internal_id]
                pretty_label = construct_pretty_label_for_row(data[INTERNAL_ID], data[ONCOTREE_CODE], data[LABEL])
                print(f"\t'{revocation_id}' ('{revocation_code}') -> '{pretty_label}'")
    else:
        print("\tNone")

    # compare all deleted and new internal ids to see if any are really the same - TODO what counts as "the same"?
    print("\nInternal ids that changed when no other data has changed ... are these really new concepts that cover different sets of cancer cases?")
    found_id_change_with_no_data_change = False
    # compare all removed ids to new ids to see if any have the same data
    for pair in {(x, y) for x in removed_internal_ids for y in new_internal_ids}:
        original_data = original_oncotree[pair[0]]
        modified_data = modified_oncotree[pair[1]]
        diff = DeepDiff(original_data, modified_data, ignore_order=True)
        # remove the change we know about (the internal id)
        diff['values_changed'] = {x : diff['values_changed'][x] for x in diff['values_changed'].keys() if x != f"root['{INTERNAL_ID}']"}
 
        if not diff['values_changed']: # TODO do we care about anything besides values_changed?
            found_id_change_with_no_data_change = True
            original_pretty_label = construct_pretty_label_for_row(original_data[INTERNAL_ID], original_data[ONCOTREE_CODE], original_data[LABEL])
            modified_pretty_label = construct_pretty_label_for_row(modified_data[INTERNAL_ID], modified_data[ONCOTREE_CODE], modified_data[LABEL])
            # TODO what changes really are important?  probably not color for example
            print(f"\t'{original_pretty_label}' -> '{modified_pretty_label}'")
    if not found_id_change_with_no_data_change:
        print("\tNone")

    # now we look at all interal ids that are in both files, what has changed about the data?
    code_change_messages = []
    parent_change_messages = []
    for internal_id in in_both_internal_ids:
        original_data = original_oncotree[internal_id]
        modified_data = modified_oncotree[internal_id]
        original_pretty_label = construct_pretty_label_for_row(original_data[INTERNAL_ID], original_data[ONCOTREE_CODE], original_data[LABEL])
        modified_pretty_label = construct_pretty_label_for_row(modified_data[INTERNAL_ID], modified_data[ONCOTREE_CODE], modified_data[LABEL])

        # confirm we have resource uri in original file, we don't have to check modified file because we check if it has changed
        if original_data[RESOURCE_URI].strip() == "":
            print(f"ERROR: Resource URI is required for all records in the original file but is missing for '{original_pretty_label}'", file=sys.stderr)
            sys.exit(1) 

        if original_data[RESOURCE_URI] != modified_data[RESOURCE_URI]:
            print(f"ERROR: Resource URI has changed for '{modified_pretty_label}', this is not allowed", file=sys.stderr)
            sys.exit(1) 

        if original_data[ONCOTREE_CODE] != modified_data[ONCOTREE_CODE]:
            code_change_messages.append(f"\t'{original_pretty_label}' -> '{modified_pretty_label}'")

        if internal_id != "ONC000001": # tissue has no parents
            # check if parent has changed
            # use oncotree codes (we will get either have the oncotree code, or will get it using the resource uri)
            modified_parent_oncotree_code = modified_data[PARENT_ONCOTREE_CODE]
            if not modified_parent_oncotree_code: 
                # then get the oncotree code using resource uri -> internal id -> oncotree code
                modified_parent_internal_id = get_parent_internal_id(internal_id,
                                                                     modified_data[PARENT_RESOURCE_URI],
                                                                     modified_data[PARENT_ONCOTREE_CODE],
                                                                     oncotree_codes_to_internal_ids,
                                                                     modified_resource_uri_to_internal_ids)
                modified_parent_oncotree_code = get_oncotree_code_from_internal_id(oncotree_codes_to_internal_ids, modified_parent_internal_id)
    
            # get the original parent oncotree code
            # in the original file we will have to look up the oncotree code using resource uri -> internal id -> oncotree code
            original_parent_internal_id = get_parent_internal_id(internal_id,
                                                                 original_data[PARENT_RESOURCE_URI],
                                                                 None, # this file doesn't have a parent oncotree code column
                                                                 oncotree_codes_to_internal_ids,
                                                                 original_resource_uri_to_internal_ids)
            original_parent_oncotree_code = get_oncotree_code_from_internal_id(oncotree_codes_to_internal_ids, original_parent_internal_id)
            if original_parent_oncotree_code != modified_parent_oncotree_code:
                parent_change_messages.append(f"\tchild: '{original_pretty_label}' parent: '{original_parent_oncotree_code}' -> child: '{modified_pretty_label}' parent: '{modified_parent_oncotree_code}'")
        

    print("\nOncotree code/label changes with no internal id change.  This is allowed as long as the new code/label covers the exact same set of cancer cases") 
    if code_change_messages:
        for message in code_change_messages:
            print(message)
    else:
        print("\tNone")

    print("\nParent change")
    if parent_change_messages:
        for message in parent_change_messages:
            print(message)
    else:
        print("\tNone")

    if not confirm_change("\nPlease confirm that all of the above changes are intentional."):
        print("ERROR: You  have said that not all changes are intentional.  Please correct your input file and run this script again.", file=sys.stderr)
        sys.exit(2)

def output_rdf_file(oncotree):
    print("TODO: output RDF file")

def get_oncotree(csv_file):
    with open(csv_file, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        internal_id_to_data = {} 
        for row in reader:
            internal_id = row[INTERNAL_ID]
            pretty_label = construct_pretty_label_for_row(internal_id, row[ONCOTREE_CODE], row[LABEL])
            # TODO move to validation section
            if row[STATUS] != 'Published':
                print(f"WARNING: do not know what to do with node '{pretty_label}' which has a status of '{row[STATUS]}', excluding it from the output file")
            internal_id_to_data[internal_id] = row
        return internal_id_to_data

def field_is_required(field, field_name, internal_id, csv_file):
    if not field:
        print(f"{field_name} is a required field, it is empty for the '{internal_id}' record in '{csv_file}'", file=sys.stderr)
        sys.exit(1)

def field_is_unique(field, field_name, column_set, internal_id, csv_file):
    # don't count "" duplicates -- these should be dealth with in required field check
    if field != "" and field in column_set:
        print(f"{field_name} must be unique.  There is more than one record with '{field}' in '{csv_file}'", file=sys.stderr)
        sys.exit(1)

def parent_resource_uri_and_label_are_valid(parent_resource_uri, parent_label, child_to_parent_resource_uris, child_uri_to_child_label, child_to_parent_labels):
    return parent_label in child_to_parent_labels \
                  and parent_label in child_to_parent_resource_uris \
                  and (child_uri_to_child_label[parent_label] == parent_label)

def validate_csv_file(csv_file, expected_header):
    # load all child->parent relationships
    # also check header and uniqueness and required values for some columns
    child_to_parent_resource_uris = {}
    child_to_parent_labels = {}
    child_uri_to_child_label = {} # make sure the parent uri + label match the child uri + label pair

    # these fields are required and must be unique
    resource_uri_set = set([])
    internal_id_set = set([])
    oncotree_code_set = set([])
    with open(csv_file, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        actual_header = reader.fieldnames
        missing_fields = set(expected_header) - set(actual_header)
        if missing_fields:
            print(f"ERROR: missing the following expected fields from input file '{csv_file}': {missing_fields}", file=sys.stderr)
            sys.exit(1)

        for row in reader:
            # save child->parent relationships
            child_to_parent_resource_uris[row[RESOURCE_URI]] = row[PARENT_RESOURCE_URI] 
            child_uri_to_child_label[row[RESOURCE_URI]] = row[LABEL]
            child_to_parent_labels[row[LABEL]] = row[PARENT_LABEL] 

            # check all colunns are not empty
            required_fields = TISSUE_NODE_REQUIRED_FIELDS if row[ONCOTREE_CODE] == "TISSUE" else REQUIRED_FIELDS
            for field in required_fields:
                field_is_required(row[field], field, row[INTERNAL_ID], csv_file)  

            # check these columns are unique
            field_is_unique(row[RESOURCE_URI], RESOURCE_URI, resource_uri_set, row[INTERNAL_ID], csv_file)
            field_is_unique(row[INTERNAL_ID], INTERNAL_ID, internal_id_set, row[ONCOTREE_CODE], csv_file)
            field_is_unique(row[ONCOTREE_CODE], ONCOTREE_CODE, oncotree_code_set, row[INTERNAL_ID], csv_file)

            resource_uri_set.add(row[RESOURCE_URI])
            internal_id_set.add(row[INTERNAL_ID])
            oncotree_code_set.add(row[ONCOTREE_CODE])

    with open(csv_file, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        label_mismatch_errors = []
        parent_invalid_errors = []
        for row in reader:
            if row[LABEL] != row[PREFERRED_LABEL]:
                label_mismatch_errors.append(f"{row[INTERNAL_ID]}: '{row[LABEL]}' != '{row[PREFERRED_LABEL]}'")
            # if this isn't the TISSUE node, we need to make sure the parent resource uri/label pair matches exists in the file
            # of course sometimes we are using the parent oncotree code intead (e.g. ALM)
            if row[ONCOTREE_CODE] != "TISSUE" and \
                parent_resource_uri_and_label_are_valid(row[PARENT_RESOURCE_URI], row[PARENT_LABEL], child_to_parent_resource_uris, child_uri_to_child_label, child_to_parent_labels):
                parent_invalid_errors.append(f"{row[INTERNAL_ID]}: URI '{row[PARENT_RESOURCE_URI]}' and label '{row[PARENT_LABEL]}'")
            elif row[ONCOTREE_CODE] == "TISSUE":
                if row[PARENT_RESOURCE_URI] or row[PARENT_LABEL] or (PARENT_ONCOTREE_CODE in row and row[PARENT_ONCOTREE_CODE]):
                    print(f"The 'TISSUE' node must not have any of these fields set: '{PARENT_RESOURCE_URI}', '{PARENT_LABEL}', '{PARENT_LABEL}' but at least one is in '{csv_file}'", file=sys.stderr)
                    sys.exit(1)

    if label_mismatch_errors:
        print(f"ERROR: '{LABEL}' and '{PREFERRED_LABEL}' columns must be identical.  Mis-matched fields in '{csv_file}':")
        for message in label_mismatch_errors:
            print(f"\t{message}")
    
    if parent_invalid_errors:
        print(f"ERROR: Invalid parents found in '{csv_file}'.  Either the parent '{PARENT_RESOURCE_URI}' or the parent '{PARENT_LABEL}' cannot be found in '{csv_file}', or the ('{PARENT_RESOURCE_URI}', '{PARENT_LABEL}') parent pair doesn't match the child  ('{RESOURCE_URI}', '{LABEL}') child pair.")
        for message in parent_invalid_errors:
            print(f"\t{message}")

    if label_mismatch_errors or parent_invalid_errors:
        sys.exit(1)

def get_internal_id_to_oncocodes():
    response = requests.get(GITHUB_RESOURCE_URI_TO_ONCOCODE_MAPPING_FILE_URL) 
    if response.status_code != 200:
        print(f"Error: Failed to download GitHub raw resource uri to oncoode file. Status code was '{response.status_code}'.  Please confirm this is the correct url: '{GITHUB_RESOURCE_URI_TO_ONCOCODE_MAPPING_FILE_URL}'", file=sys.stderr)
        sys.exit(1)
    internal_id_to_oncocodes = {}
    for row in response.text.splitlines():
        fields = row.split()
        if fields[1] == "hasCode":
            internal_id_to_oncocodes[fields[0]] = fields[2]    
    return internal_id_to_oncocodes
 
def usage(parser, message):
    if message:
        print(message, file=sys.stderr)
    parser.print_help(file=sys.stderr)
    sys.exit(1)

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--original-file", help = f"Original csv file from Graphite. {HELP_FOR_FILE_FORMAT}", required = True)
    parser.add_argument("-m", "--modified-file", help = f"Modified csv file from user.  This should be a modified copy of the original csv file from Graphite, with an additional column at the end called '{PARENT_ONCOTREE_CODE}'.", required = True)
    args = parser.parse_args()

    original_file = args.original_file
    modified_file = args.modified_file

    if not original_file or not modified_file: 
        usage(parser, f"ERROR: missing file arguments, given original file '{original_file}' and modified file '{modified_file}'")

    if not os.path.isfile(original_file):
        usage(parser, f"ERROR: cannot access original file {original_file}")
        sys.exit(1)

    if not os.path.isfile(modified_file):
        usage(parser, f"ERROR: cannot access modified file {modified_file}")
        sys.exit(1)
    return original_file, modified_file

def main():
    original_file, modified_file = get_args()
    validate_csv_file(original_file, EXPECTED_HEADER)
    validate_csv_file(modified_file, EXPECTED_HEADER_MODIFIED_FILE)
    original_oncotree = get_oncotree(original_file)
    modified_oncotree = get_oncotree(modified_file)
    internal_id_to_oncocodes = get_internal_id_to_oncocodes()
    # get_all_precursors, get_all_revocations, get_resource_uri_to_internal_ids, get_oncotree_codes_to_resource_uris could be combined into one function
    # we aren't reading the file over and over but this seems clearer
    precursor_id_to_internal_ids = get_all_precursors(modified_file)
    revocation_id_to_internal_ids = get_all_revocations(modified_file)
    original_resource_uri_to_internal_ids = get_resource_uri_to_internal_ids(original_file)
    modified_resource_uri_to_internal_ids = get_resource_uri_to_internal_ids(modified_file)
    oncotree_codes_to_internal_ids = get_oncotree_codes_to_internal_ids(modified_file)
    confirm_changes(original_oncotree,
                    modified_oncotree,
                    precursor_id_to_internal_ids,
                    revocation_id_to_internal_ids,
                    original_resource_uri_to_internal_ids,
                    modified_resource_uri_to_internal_ids,
                    internal_id_to_oncocodes,
                    oncotree_codes_to_internal_ids)
    output_rdf_file(modified_oncotree)

if __name__ == '__main__':
   main()
