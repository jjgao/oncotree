# Copyright (c) 2025 Memorial Sloan-Kettering Cancer Center.                   
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

import uuid

CSV_LABEL = "Primary Concept"
CSV_RESOURCE_URI = "Resource URI"
CSV_ONCOTREE_CODE = "notation (SKOS)"
CSV_SCHEME_URI = "skos:inScheme URI"
CSV_STATUS = "Status"   
CSV_INTERNAL_ID = "clinicalCasesSubset (OncoTree Tumor Type)"
CSV_COLOR = "color (OncoTree Tumor Type)"
CSV_MAIN_TYPE = "mainType (OncoTree Tumor Type)"
CSV_PRECURSORS = "precursors (OncoTree Tumor Type)"
CSV_PREFERRED_LABEL = "preferred label (SKOS)"
CSV_REVOCATIONS = "revocations (OncoTree Tumor Type)"
CSV_PARENT_RESOURCE_URI = "has broader (SKOS) URI"
CSV_PARENT_LABEL = "has broader (SKOS)"
CSV_PARENT_ONCOTREE_CODE = "parent oncotree code"

RDF_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF
    xmlns:ottt="http://data.mskcc.org/ontologies/oncotree#"
    xmlns:skos="http://www.w3.org/2004/02/skos/core#"
    xmlns:graphite="http://schema.synaptica.com/oasis#"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
    xmlns:rdf4j="http://rdf4j.org/schema/rdf4j#"
    xmlns:sesame="http://www.openrdf.org/schema/sesame#"
    xmlns:owl="http://www.w3.org/2002/07/owl#"
    xmlns:fn="http://www.w3.org/2005/xpath-functions#">
"""
RDF_FOOTER = "</rdf:RDF>"
RESOURCE_URI_BASE = "https://data.mskcc.org/ontologies/oncotree#"
RDF_RECORD_FIXED_FIELDS = """\t<rdf:type rdf:resource="http://schema.synaptica.com/oasis#Concept"/>
	<rdf:type rdf:resource="http://www.w3.org/2004/02/skos/core#Concept"/>
	<skos:inScheme rdf:resource="https://preprod3.msk.synaptica.net/concept_scheme/b4b33e88-6dcd-5c88-375b-25d629e822f6"/>
	<graphite:hasTemplate rdf:resource="https://preprod3.msk.synaptica.net/template/fe5efc47-d308-4415-a834-525f5fb792c3"/>
	<graphite:conceptStatus>Published</graphite:conceptStatus>"""

def write_header(out_file):
    print(RDF_HEADER, file=out_file)

#<rdf:Description rdf:about="https://data.mskcc.org/ontologies/oncotree#dca88347-5939-4c23-8a19-e4a1db414240">
#    <rdf:type rdf:resource="http://schema.synaptica.com/oasis#Concept"/>
#    <rdf:type rdf:resource="http://www.w3.org/2004/02/skos/core#Concept"/>
#    <rdfs:label xml:lang="en">T-Lymphoblastic Leukemia/Lymphoma</rdfs:label>
#    <skos:inScheme rdf:resource="https://preprod3.msk.synaptica.net/concept_scheme/b4b33e88-6dcd-5c88-375b-25d629e822f6"/>
#    <graphite:hasTemplate rdf:resource="https://preprod3.msk.synaptica.net/template/fe5efc47-d308-4415-a834-525f5fb792c3"/>
#    <graphite:conceptStatus>Published</graphite:conceptStatus>
#    <skos:prefLabel xml:lang="en">T-Lymphoblastic Leukemia/Lymphoma</skos:prefLabel>
#    <skos:notation xml:lang="en">TLL</skos:notation> 
#    <ottt:color xml:lang="en">LimeGreen</ottt:color>
#    <ottt:maintype xml:lang="en">T-Lymphoblastic Leukemia/Lymphoma</ottt:maintype>
#    <ottt:precursors xml:lang="en">ONC000041</ottt:precursors>
#    <ottt:revocations xml:lang="en">ONC000038</ottt:revocations>
#    <ottt:clinicalcasessubset xml:lang="en">ONC000744</ottt:clinicalcasessubset>
#    <skos:broader rdf:resource="https://data.mskcc.org/ontologies/oncotree#35233f33-9d05-42fb-8d0e-4823dcc3a2a2"/>
#</rdf:Description>

def generate_resource_uri():
    """Generates a new resource uri"""
    return RESOURCE_URI_BASE + str(uuid.uuid4())

def write_records(oncotree, oncotree_code_to_resource_uris, out_file):
    for row in oncotree.values():
        print(f"<rdf:Description rdf:about=\"{row[CSV_RESOURCE_URI]}\">", file=out_file)
        print(RDF_RECORD_FIXED_FIELDS, file=out_file)
        print(f"	<rdfs:label xml:lang=\"en\">{row[CSV_LABEL]}</rdfs:label>", file=out_file)
        print(f"    <skos:prefLabel xml:lang=\"en\">{row[CSV_PREFERRED_LABEL]}</skos:prefLabel>", file=out_file)
        print(f"    <skos:notation xml:lang=\"en\">{row[CSV_ONCOTREE_CODE]}</skos:notation>", file=out_file)
        if row[CSV_COLOR]:
            print(f"    <ottt:color xml:lang=\"en\">{row[CSV_COLOR]}</ottt:color>", file=out_file)
        if row[CSV_MAIN_TYPE]:
            print(f"    <ottt:maintype xml:lang=\"en\">{row[CSV_MAIN_TYPE]}</ottt:maintype>", file=out_file)
        if row[CSV_PRECURSORS]:
            print(f"    <ottt:precursors xml:lang=\"en\">{row[CSV_PRECURSORS]}</ottt:precursors>", file=out_file)
        if row[CSV_REVOCATIONS]:
            print(f"    <ottt:revocations xml:lang=\"en\">{row[CSV_REVOCATIONS]}</ottt:revocations>", file=out_file)
        print(f"    <ottt:clinicalcasessubset xml:lang=\"en\">{row[CSV_INTERNAL_ID]}</ottt:clinicalcasessubset>", file=out_file)
        if row[CSV_ONCOTREE_CODE] == "TISSUE":
            print(f"	<skos:topConceptOf rdf:resource=\"https://preprod3.msk.synaptica.net/concept_scheme/b4b33e88-6dcd-5c88-375b-25d629e822f6\"/>", file=out_file) 
        else:
            parent_resource_uri = row[CSV_PARENT_RESOURCE_URI] if row[CSV_PARENT_RESOURCE_URI] else oncotree_code_to_resource_uris[row[CSV_PARENT_ONCOTREE_CODE]]
            print(f"    <skos:broader rdf:resource=\"{parent_resource_uri}\"/>", file=out_file)
        print("</rdf:Description>\n", file=out_file)

def write_footer(out_file):
    print(RDF_FOOTER, file=out_file)

def get_oncotree_code_to_resource_uris(oncotree):
    oncotree_code_to_resource_uris = {}
    for row in oncotree.values():
        oncotree_code_to_resource_uris[row[CSV_ONCOTREE_CODE]] = row[CSV_RESOURCE_URI]
    return oncotree_code_to_resource_uris

def populate_all_resource_uris(oncotree):
    for row in oncotree.values():
        if not row[CSV_RESOURCE_URI]:
            row[CSV_RESOURCE_URI] = generate_resource_uri()

def write_rdf(oncotree, out_filename):
    """Write an RDF to a file"""
    populate_all_resource_uris(oncotree) # this fills in the empty resource uris with new ones (these should be new records)
    oncotree_code_to_resource_uris = get_oncotree_code_to_resource_uris(oncotree)
    with open(out_filename, "w") as out_file:
        write_header(out_file)
        write_records(oncotree, oncotree_code_to_resource_uris, out_file)
        write_footer(out_file)
