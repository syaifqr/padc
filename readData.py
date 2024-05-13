import xml.etree.ElementTree as ET
import pysmile
import pysmile_license
import random
import itertools
import numpy as np

tree = ET.parse('padc2.xml')
root = tree.getroot()

individuals_list = []
entity_types = ["Hama", "Penyakit"]

for individual in root.findall(".//{http://www.w3.org/2002/07/owl#}NamedIndividual"):
    individual_type_tags = individual.findall(
        ".//{http://www.w3.org/1999/02/22-rdf-syntax-ns#}type")

    for type_tag in individual_type_tags:
        type_value = type_tag.attrib['{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource']
        if any(type_value.endswith(entity_type) for entity_type in entity_types):
            # if type_value.endswith("Hama"):
            individual_dict = {}
            individual_value = individual.attrib['{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about']
            value_after_hash = individual_value.split("#")[1]
            individual_dict['nama'] = value_after_hash

            menyebabkan_gejala_tags = individual.findall(
                ".//{http://www.semanticweb.org/syaifulqomaruddin/ontologies/2024/0/padc#}menyebabkanGejala")

            values = [tag.attrib['{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource'].split(
                '#')[1] for tag in menyebabkan_gejala_tags]

            individual_dict['gejala'] = values
            individuals_list.append(individual_dict)

a = 1
r_value = "R000"
rule_list = []

namespaces = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "swrl": "http://www.w3.org/2003/11/swrl#"
}
while a < 52:
    individu_dict = {}
    # Menghitung nilai R
    # Mengambil angka setelah huruf "R" dan menambahkan satu
    r_value = int(r_value[1:]) + 1
    r_label = f"R{r_value:03d}"  # Format label kembali dengan tiga digit

    individu_dict['rule'] = r_label
    r_value = r_label
    a += 1

    # Find the rule with label "R022"
    target_rule_label = r_label
    target_rule = None

    for description in root.findall(".//rdf:Description", namespaces=namespaces):
        label_element = description.find("rdfs:label", namespaces=namespaces)
        if label_element is not None and label_element.text == target_rule_label:
            target_rule = description
            break

    if target_rule is not None:
        def extract_value(uri):
            return uri.split('#')[-1] if uri is not None else "Not found"
        # Extract values from the rule body and head
        nama_gejala = target_rule.find(
            ".//swrl:argument2[@rdf:resource]", namespaces=namespaces)
        ekstraksi_gejala = extract_value(nama_gejala.get(
            '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource'))
        individu_dict['gejala'] = ekstraksi_gejala

        nama_serangan = target_rule.find(
            ".//swrl:head/rdf:Description/rdf:first/rdf:Description/swrl:argument1[@rdf:resource]", namespaces=namespaces)
        ekstraksi_nama = extract_value(nama_serangan.get(
            '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource'))
        individu_dict['nama'] = ekstraksi_nama

        risk_value = target_rule.find(
            ".//swrl:argument2[@rdf:datatype='http://www.w3.org/2001/XMLSchema#float']", namespaces=namespaces)
        ekstraksi_skor = risk_value.text if risk_value is not None else "Not found"
        individu_dict['skor'] = ekstraksi_skor

        rule_list.append(individu_dict)
    else:
        print(f"Rule with label {target_rule_label} not found.")

# print(individuals_list)
# print(rule_list)


# Membuat Bayesian Network
net = pysmile.Network()

nodes = {}

# Mengisi dictionary gejala_skor

for item in individuals_list:
    name = item['nama']
    gejala = item['gejala']

    # Membuat parent node untuk nama
    if name not in nodes:
        x = random.randint(0, 1000)  # Ubah batas sesuai kebutuhan Anda
        y = random.randint(0, 1000)
        nodes[name] = net.add_node(pysmile.NodeType.CPT, name)
        net.set_node_position(nodes[name], x, y, 85, 55)

        net.set_outcome_id(nodes[name], 0, "absent")
        net.set_outcome_id(nodes[name], 1, "present")

    # Menambahkan parent node ke variabel nodes
    parent_node = nodes[name]

    # Membuat child node untuk gejala
    for symptom in gejala:
        if symptom not in nodes:
            a = random.randint(0, 500)  # Ubah batas sesuai kebutuhan Anda
            b = random.randint(0, 500)
            nodes[symptom] = net.add_node(pysmile.NodeType.CPT, symptom)
            net.set_node_position(nodes[symptom], a, b, 85, 55)

            net.set_outcome_id(nodes[symptom], 0, "absent")
            net.set_outcome_id(nodes[symptom], 1, "present")

        # Menambahkan koneksi antara nama (parent) dan gejala (child)
        child_node = nodes[symptom]
        net.add_arc(parent_node, child_node)

for z in net.get_all_nodes():
    node_handle = z
    name_node = net.get_node_name(node_handle)
    childs_id = net.get_child_ids(node_handle)
    parents_id = net.get_parent_ids(node_handle)
    if len(parents_id) > 0 and len(childs_id) > 0:
        # if name_node in temp_list:
        print(name_node)
        cpt = net.get_node_definition(name_node)
        parents = net.get_parents(name_node)
        dim_count = 1 + len(parents)
        dim_sizes = [0] * dim_count
        for i in range(0, dim_count - 1):
            dim_sizes[i] = net.get_outcome_count(parents[i])
        dim_sizes[len(dim_sizes) - 1] = net.get_outcome_count(name_node)
        coords = [0] * dim_count
        final_scores = []
        for elem_idx in range(0, len(cpt)):
            prod = 1
            for i in range(len(dim_sizes) - 1, -1, -1):
                coords[i] = int(elem_idx / prod) % dim_sizes[i]
                prod *= dim_sizes[i]
            outcome = net.get_outcome_id(
                name_node, coords[dim_count - 1])
            cek = []
            temp_cek = []
            if outcome == "absent":
                print(outcome)
                for parent_idx in range(0, len(parents)):
                    ceks = {}
                    ceklist = {}
                    parent_handle = parents[parent_idx]
                    gg = net.get_node_id(parent_handle)
                    cc = net.get_outcome_id(
                        parent_handle, coords[parent_idx])
                    ceks['nama'] = gg
                    ceks['cc'] = cc
                    ceklist['nama'] = gg
                    ceklist['cc'] = cc
                    cek.append(ceks)
                    temp_cek.append(ceklist)
                if len(cek) == 1:
                    if cek[0]['nama'] == temp_cek[0]['nama'] and cek[0]['cc'] == temp_cek[0]['cc']:
                        a = cek[0]['nama']
                        score = []
                        for rule in rule_list:
                            if rule['nama'] == name_node and cek[0]['cc'] == "absent" and rule['gejala'] == a:
                                x = 0.4
                                y = 1 - x
                                score = [y]
                            elif rule['nama'] == name_node and cek[0]['cc'] == "present" and rule['gejala'] == a:
                                x = float(rule['skor'])
                                y = 1 - x
                                score = [y]
                        final_scores.append(score[0])
                        print(score)
                        print(cek[0]['nama'], cek[0]['cc'])
            if outcome == "present":
                print(outcome)
                for parent_idx in range(0, len(parents)):
                    ceks = {}
                    ceklist = {}
                    parent_handle = parents[parent_idx]
                    gg = net.get_node_id(parent_handle)
                    cc = net.get_outcome_id(
                        parent_handle, coords[parent_idx])
                    ceks['nama'] = gg
                    ceks['cc'] = cc
                    ceklist['nama'] = gg
                    ceklist['cc'] = cc
                    cek.append(ceks)
                    temp_cek.append(ceklist)
                if len(cek) == 1:
                    if cek[0]['nama'] == temp_cek[0]['nama'] and cek[0]['cc'] == temp_cek[0]['cc']:
                        a = cek[0]['nama']
                        score = []
                        for rule in rule_list:
                            if rule['nama'] == name_node and cek[0]['cc'] == "absent" and rule['gejala'] == a:
                                x = 0.4
                                score = [x]
                            elif rule['nama'] == name_node and cek[0]['cc'] == "present" and rule['gejala'] == a:
                                x = float(rule['skor'])
                                score = [x]
                        final_scores.append(score[0])
                        print(score)
                        print(cek[0]['nama'], cek[0]['cc'])
        print(final_scores)
        net.set_node_definition(name_node, final_scores)

    elif len(parents_id) > 0:
        # if name_node in temp_list:
        print(name_node)
        cpt = net.get_node_definition(name_node)
        parents = net.get_parents(name_node)
        dim_count = 1 + len(parents)
        dim_sizes = [0] * dim_count
        for i in range(0, dim_count - 1):
            dim_sizes[i] = net.get_outcome_count(parents[i])
        dim_sizes[len(dim_sizes) - 1] = net.get_outcome_count(name_node)
        coords = [0] * dim_count
        final_scores = []
        for elem_idx in range(0, len(cpt)):
            prod = 1
            for i in range(len(dim_sizes) - 1, -1, -1):
                coords[i] = int(elem_idx / prod) % dim_sizes[i]
                prod *= dim_sizes[i]
            outcome = net.get_outcome_id(
                name_node, coords[dim_count - 1])
            cek = []
            temp_cek = []
            if outcome == "absent":
                print(outcome)
                for parent_idx in range(0, len(parents)):
                    ceks = {}
                    ceklist = {}
                    parent_handle = parents[parent_idx]
                    gg = net.get_node_id(parent_handle)
                    cc = net.get_outcome_id(
                        parent_handle, coords[parent_idx])
                    ceks['nama'] = gg
                    ceks['cc'] = cc
                    ceklist['nama'] = gg
                    ceklist['cc'] = cc
                    cek.append(ceks)
                    temp_cek.append(ceklist)
                if len(cek) == 1:
                    if cek[0]['nama'] == temp_cek[0]['nama'] and cek[0]['cc'] == temp_cek[0]['cc']:
                        a = cek[0]['nama']
                        score = []
                        for rule in rule_list:
                            if rule['nama'] == a and cek[0]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = 0.05
                                y = 1 - x
                                score = [y]
                            elif rule['nama'] == a and cek[0]['cc'] == "present" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                y = 1 - x
                                score = [y]
                        final_scores.append(score[0])
                        print(score)
                        print(cek[0]['nama'], cek[0]['cc'])
                if len(cek) == 2:
                    if cek[0]['nama'] == temp_cek[0]['nama'] and cek[0]['cc'] == temp_cek[0]['cc'] and cek[1]['nama'] == temp_cek[1]['nama'] and cek[1]['cc'] == temp_cek[1]['cc']:
                        a = cek[0]['nama']
                        b = cek[1]['nama']
                        score = []
                        total_skor = 0
                        for rule in rule_list:
                            if rule['nama'] == a and cek[0]['cc'] == "present" and cek[1]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                y = 1 - x
                                score.append(y)
                            elif rule['nama'] == b and cek[0]['cc'] == "absent" and cek[1]['cc'] == "present" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                y = 1 - x
                                score.append(y)
                            elif rule['nama'] == a and cek[0]['cc'] == "absent" and cek[1]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = 0.05
                                y = 1 - x
                                score.append(y)
                            elif ((rule['nama'] == a or rule['nama'] == b) and rule['nama'] in [cek[0]['nama'], cek[1]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                z = 1 - x
                                y = round(z, 3)
                                score = [y]
                        final_scores.append(score[0])
                        print(score)
                        print(cek[0]['nama'], cek[0]['cc'],
                              cek[1]['nama'], cek[1]['cc'])
                elif len(cek) == 3:
                    if cek[0]['nama'] == temp_cek[0]['nama'] and cek[0]['cc'] == temp_cek[0]['cc'] and cek[1]['nama'] == temp_cek[1]['nama'] and cek[1]['cc'] == temp_cek[1]['cc'] and cek[2]['nama'] == temp_cek[2]['nama'] and cek[2]['cc'] == temp_cek[2]['cc']:
                        a = cek[0]['nama']
                        b = cek[1]['nama']
                        c = cek[2]['nama']
                        score = []
                        total_skor = 0
                        for rule in rule_list:
                            if rule['nama'] == a and cek[0]['cc'] == "absent" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = 0.05
                                y = 1 - x
                                score.append(y)
                            elif rule['nama'] == a and cek[0]['cc'] == "present" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                y = 1 - x
                                score.append(y)
                            elif rule['nama'] == b and cek[0]['cc'] == "absent" and cek[1]['cc'] == "present" and cek[2]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                y = 1 - x
                                score.append(y)
                            elif rule['nama'] == c and cek[0]['cc'] == "absent" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "present" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                y = 1 - x
                                score.append(y)
                            elif ((rule['nama'] == a or rule['nama'] == b) and rule['nama'] in [cek[0]['nama'], cek[1]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "present" and cek[2]['cc'] == "absent" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                z = 1 - x
                                y = round(z, 3)
                                score = [y]
                            elif ((rule['nama'] == b or rule['nama'] == c) and rule['nama'] in [cek[1]['nama'], cek[2]['nama']]) and cek[0]['cc'] == "absent" and cek[1]['cc'] == "present" and cek[2]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                z = 1 - x
                                y = round(z, 3)
                                score = [y]
                            elif ((rule['nama'] == a or rule['nama'] == c) and rule['nama'] in [cek[0]['nama'], cek[2]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                z = 1 - x
                                y = round(z, 3)
                                score = [y]
                            elif ((rule['nama'] == a or rule['nama'] == b or rule['nama'] == c) and rule['nama'] in [cek[0]['nama'], cek[1]['nama'], cek[2]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "present" and cek[2]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/3
                                z = 1 - x
                                y = round(z, 3)
                                score = [y]
                        final_scores.append(score[0])
                        print(score)
                        print(cek[0]['nama'], cek[0]['cc'],
                              cek[1]['nama'], cek[1]['cc'],
                              cek[2]['nama'], cek[2]['cc'])
                elif len(cek) == 4:
                    if cek[0]['nama'] == temp_cek[0]['nama'] and cek[0]['cc'] == temp_cek[0]['cc'] and cek[1]['nama'] == temp_cek[1]['nama'] and cek[1]['cc'] == temp_cek[1]['cc'] and cek[2]['nama'] == temp_cek[2]['nama'] and cek[2]['cc'] == temp_cek[2]['cc'] and cek[3]['nama'] == temp_cek[3]['nama'] and cek[3]['cc'] == temp_cek[3]['cc']:
                        a = cek[0]['nama']
                        b = cek[1]['nama']
                        c = cek[2]['nama']
                        d = cek[3]['nama']
                        score = []
                        total_skor = 0
                        for rule in rule_list:
                            if rule['nama'] == a and cek[0]['cc'] == "absent" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "absent" and cek[3]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = 0.05
                                y = 1 - x
                                score.append(y)
                            elif rule['nama'] == a and cek[0]['cc'] == "present" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "absent" and cek[3]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                y = 1 - x
                                score.append(y)
                            elif rule['nama'] == b and cek[0]['cc'] == "absent" and cek[1]['cc'] == "present" and cek[2]['cc'] == "absent" and cek[3]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                y = 1 - x
                                score.append(y)
                            elif rule['nama'] == c and cek[0]['cc'] == "absent" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "present" and cek[3]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                y = 1 - x
                                score.append(y)
                            elif rule['nama'] == d and cek[0]['cc'] == "absent" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "absent" and cek[3]['cc'] == "present" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                y = 1 - x
                                score.append(y)
                            elif ((rule['nama'] == a or rule['nama'] == b) and rule['nama'] in [cek[0]['nama'], cek[1]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "present" and cek[2]['cc'] == "absent" and cek[3]['cc'] == "absent" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                z = 1 - x
                                y = round(z, 3)
                                score = [y]
                            elif ((rule['nama'] == b or rule['nama'] == c) and rule['nama'] in [cek[1]['nama'], cek[2]['nama']]) and cek[0]['cc'] == "absent" and cek[1]['cc'] == "present" and cek[2]['cc'] == "present" and cek[3]['cc'] == "absent" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                z = 1 - x
                                y = round(z, 3)
                                score = [y]
                            elif ((rule['nama'] == a or rule['nama'] == c) and rule['nama'] in [cek[0]['nama'], cek[2]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "present" and cek[3]['cc'] == "absent" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                z = 1 - x
                                y = round(z, 3)
                                score = [y]
                            elif ((rule['nama'] == a or rule['nama'] == d) and rule['nama'] in [cek[0]['nama'], cek[3]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "absent" and cek[3]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                z = 1 - x
                                y = round(z, 3)
                                score = [y]
                            elif ((rule['nama'] == b or rule['nama'] == d) and rule['nama'] in [cek[1]['nama'], cek[3]['nama']]) and cek[0]['cc'] == "absent" and cek[1]['cc'] == "present" and cek[2]['cc'] == "absent" and cek[3]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                z = 1 - x
                                y = round(z, 3)
                                score = [y]
                            elif ((rule['nama'] == c or rule['nama'] == d) and rule['nama'] in [cek[2]['nama'], cek[3]['nama']]) and cek[0]['cc'] == "absent" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "present" and cek[3]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                z = 1 - x
                                y = round(z, 3)
                                score = [y]
                            elif ((rule['nama'] == a or rule['nama'] == b or rule['nama'] == c) and rule['nama'] in [cek[0]['nama'], cek[1]['nama'], cek[2]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "present" and cek[2]['cc'] == "present" and cek[3]['cc'] == "absent" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/3
                                z = 1 - x
                                y = round(z, 3)
                                score = [y]
                            elif ((rule['nama'] == a or rule['nama'] == c or rule['nama'] == d) and rule['nama'] in [cek[0]['nama'], cek[2]['nama'], cek[3]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "present" and cek[3]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/3
                                z = 1 - x
                                y = round(z, 3)
                                score = [y]
                            elif ((rule['nama'] == b or rule['nama'] == c or rule['nama'] == d) and rule['nama'] in [cek[1]['nama'], cek[2]['nama'], cek[3]['nama']]) and cek[0]['cc'] == "absent" and cek[1]['cc'] == "present" and cek[2]['cc'] == "present" and cek[3]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/3
                                z = 1 - x
                                y = round(z, 3)
                                score = [y]
                            elif ((rule['nama'] == a or rule['nama'] == b or rule['nama'] == d) and rule['nama'] in [cek[0]['nama'], cek[1]['nama'], cek[3]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "present" and cek[2]['cc'] == "absent" and cek[3]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/3
                                z = 1 - x
                                y = round(z, 3)
                                score = [y]
                            elif ((rule['nama'] == a or rule['nama'] == b or rule['nama'] == c or rule['nama'] == d) and rule['nama'] in [cek[0]['nama'], cek[1]['nama'], cek[2]['nama'], cek[3]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "present" and cek[2]['cc'] == "present" and cek[3]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/4
                                z = 1 - x
                                y = round(z, 3)
                                score = [y]
                        final_scores.append(score[0])
                        print(score)
                        print(cek[0]['nama'], cek[0]['cc'],
                              cek[1]['nama'], cek[1]['cc'],
                              cek[2]['nama'], cek[2]['cc'],
                              cek[3]['nama'], cek[3]['cc'])
            elif outcome == "present":
                print(outcome)
                for parent_idx in range(0, len(parents)):
                    ceks = {}
                    ceklist = {}
                    parent_handle = parents[parent_idx]
                    gg = net.get_node_id(parent_handle)
                    cc = net.get_outcome_id(
                        parent_handle, coords[parent_idx])
                    ceks['nama'] = gg
                    ceks['cc'] = cc
                    ceklist['nama'] = gg
                    ceklist['cc'] = cc
                    cek.append(ceks)
                    temp_cek.append(ceklist)
                if len(cek) == 1:
                    if cek[0]['nama'] == temp_cek[0]['nama'] and cek[0]['cc'] == temp_cek[0]['cc']:
                        a = cek[0]['nama']
                        score = []
                        for rule in rule_list:
                            if rule['nama'] == a and cek[0]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = 0.05
                                score = [x]
                            elif rule['nama'] == a and cek[0]['cc'] == "present" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                y = 0.5
                                score = [x]
                        final_scores.append(score[0])
                        print(score)
                        print(cek[0]['nama'], cek[0]['cc'])
                elif len(cek) == 2:
                    if cek[0]['nama'] == temp_cek[0]['nama'] and cek[0]['cc'] == temp_cek[0]['cc'] and cek[1]['nama'] == temp_cek[1]['nama'] and cek[1]['cc'] == temp_cek[1]['cc']:
                        a = cek[0]['nama']
                        b = cek[1]['nama']
                        score = []
                        total_skor = 0
                        for rule in rule_list:
                            if rule['nama'] == a and cek[0]['cc'] == "present" and cek[1]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                score.append(x)
                            elif rule['nama'] == b and cek[0]['cc'] == "absent" and cek[1]['cc'] == "present" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                score.append(x)
                            elif rule['nama'] == a and cek[0]['cc'] == "absent" and cek[1]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = 0.05
                                score.append(x)
                            elif ((rule['nama'] == a or rule['nama'] == b) and rule['nama'] in [cek[0]['nama'], cek[1]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                score = [x]
                        final_scores.append(score[0])
                        print(score)
                        print(cek[0]['nama'], cek[0]['cc'],
                              cek[1]['nama'], cek[1]['cc'])
                elif len(cek) == 3:
                    if cek[0]['nama'] == temp_cek[0]['nama'] and cek[0]['cc'] == temp_cek[0]['cc'] and cek[1]['nama'] == temp_cek[1]['nama'] and cek[1]['cc'] == temp_cek[1]['cc'] and cek[2]['nama'] == temp_cek[2]['nama'] and cek[2]['cc'] == temp_cek[2]['cc']:
                        a = cek[0]['nama']
                        b = cek[1]['nama']
                        c = cek[2]['nama']
                        score = []
                        total_skor = 0
                        for rule in rule_list:
                            if rule['nama'] == a and cek[0]['cc'] == "absent" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = 0.05
                                score.append(x)
                            elif rule['nama'] == a and cek[0]['cc'] == "present" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                score.append(x)
                            elif rule['nama'] == b and cek[0]['cc'] == "absent" and cek[1]['cc'] == "present" and cek[2]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                score.append(x)
                            elif rule['nama'] == c and cek[0]['cc'] == "absent" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "present" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                score.append(x)
                            elif ((rule['nama'] == a or rule['nama'] == b) and rule['nama'] in [cek[0]['nama'], cek[1]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "present" and cek[2]['cc'] == "absent" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                y = round(x, 3)
                                score = [y]
                            elif ((rule['nama'] == b or rule['nama'] == c) and rule['nama'] in [cek[1]['nama'], cek[2]['nama']]) and cek[0]['cc'] == "absent" and cek[1]['cc'] == "present" and cek[2]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                y = round(x, 3)
                                score = [y]
                            elif ((rule['nama'] == a or rule['nama'] == c) and rule['nama'] in [cek[0]['nama'], cek[2]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                y = round(x, 3)
                                score = [y]
                            elif ((rule['nama'] == a or rule['nama'] == b or rule['nama'] == c) and rule['nama'] in [cek[0]['nama'], cek[1]['nama'], cek[2]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "present" and cek[2]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/3
                                y = round(x, 3)
                                score = [y]
                        final_scores.append(score[0])
                        print(score)
                        print(cek[0]['nama'], cek[0]['cc'],
                              cek[1]['nama'], cek[1]['cc'],
                              cek[2]['nama'], cek[2]['cc'])
                elif len(cek) == 4:
                    if cek[0]['nama'] == temp_cek[0]['nama'] and cek[0]['cc'] == temp_cek[0]['cc'] and cek[1]['nama'] == temp_cek[1]['nama'] and cek[1]['cc'] == temp_cek[1]['cc'] and cek[2]['nama'] == temp_cek[2]['nama'] and cek[2]['cc'] == temp_cek[2]['cc'] and cek[3]['nama'] == temp_cek[3]['nama'] and cek[3]['cc'] == temp_cek[3]['cc']:
                        a = cek[0]['nama']
                        b = cek[1]['nama']
                        c = cek[2]['nama']
                        d = cek[3]['nama']
                        score = []
                        total_skor = 0
                        for rule in rule_list:
                            if rule['nama'] == a and cek[0]['cc'] == "absent" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "absent" and cek[3]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = 0.05
                                score.append(x)
                            elif rule['nama'] == a and cek[0]['cc'] == "present" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "absent" and cek[3]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                score.append(x)
                            elif rule['nama'] == b and cek[0]['cc'] == "absent" and cek[1]['cc'] == "present" and cek[2]['cc'] == "absent" and cek[3]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                score.append(x)
                            elif rule['nama'] == c and cek[0]['cc'] == "absent" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "present" and cek[3]['cc'] == "absent" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                score.append(x)
                            elif rule['nama'] == d and cek[0]['cc'] == "absent" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "absent" and cek[3]['cc'] == "present" and rule['gejala'] == name_node:
                                x = float(rule['skor'])
                                score.append(x)
                            elif ((rule['nama'] == a or rule['nama'] == b) and rule['nama'] in [cek[0]['nama'], cek[1]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "present" and cek[2]['cc'] == "absent" and cek[3]['cc'] == "absent" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                y = round(x, 3)
                                score = [y]
                            elif ((rule['nama'] == b or rule['nama'] == c) and rule['nama'] in [cek[1]['nama'], cek[2]['nama']]) and cek[0]['cc'] == "absent" and cek[1]['cc'] == "present" and cek[2]['cc'] == "present" and cek[3]['cc'] == "absent" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                y = round(x, 3)
                                score = [y]
                            elif ((rule['nama'] == a or rule['nama'] == c) and rule['nama'] in [cek[0]['nama'], cek[2]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "present" and cek[3]['cc'] == "absent" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                y = round(x, 3)
                                score = [y]
                            elif ((rule['nama'] == a or rule['nama'] == d) and rule['nama'] in [cek[0]['nama'], cek[3]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "absent" and cek[3]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                y = round(x, 3)
                                score = [x]
                            elif ((rule['nama'] == b or rule['nama'] == d) and rule['nama'] in [cek[1]['nama'], cek[3]['nama']]) and cek[0]['cc'] == "absent" and cek[1]['cc'] == "present" and cek[2]['cc'] == "absent" and cek[3]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                y = round(x, 3)
                                score = [y]
                            elif ((rule['nama'] == c or rule['nama'] == d) and rule['nama'] in [cek[2]['nama'], cek[3]['nama']]) and cek[0]['cc'] == "absent" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "present" and cek[3]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/2
                                y = round(x, 3)
                                score = [y]
                            elif ((rule['nama'] == a or rule['nama'] == b or rule['nama'] == c) and rule['nama'] in [cek[0]['nama'], cek[1]['nama'], cek[2]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "present" and cek[2]['cc'] == "present" and cek[3]['cc'] == "absent" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/3
                                y = round(x, 3)
                                score = [y]
                            elif ((rule['nama'] == a or rule['nama'] == c or rule['nama'] == d) and rule['nama'] in [cek[0]['nama'], cek[2]['nama'], cek[3]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "absent" and cek[2]['cc'] == "present" and cek[3]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/3
                                y = round(x, 3)
                                score = [y]
                            elif ((rule['nama'] == b or rule['nama'] == c or rule['nama'] == d) and rule['nama'] in [cek[1]['nama'], cek[2]['nama'], cek[3]['nama']]) and cek[0]['cc'] == "absent" and cek[1]['cc'] == "present" and cek[2]['cc'] == "present" and cek[3]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/3
                                y = round(x, 3)
                                score = [y]
                            elif ((rule['nama'] == a or rule['nama'] == b or rule['nama'] == d) and rule['nama'] in [cek[0]['nama'], cek[1]['nama'], cek[3]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "present" and cek[2]['cc'] == "absent" and cek[3]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/3
                                y = round(x, 3)
                                score = [y]
                            elif ((rule['nama'] == a or rule['nama'] == b or rule['nama'] == c or rule['nama'] == d) and rule['nama'] in [cek[0]['nama'], cek[1]['nama'], cek[2]['nama'], cek[3]['nama']]) and cek[0]['cc'] == "present" and cek[1]['cc'] == "present" and cek[2]['cc'] == "present" and cek[3]['cc'] == "present" and rule['gejala'] == name_node:
                                total_skor += float(rule['skor'])
                                x = total_skor/4
                                y = round(x, 3)
                                score = [y]
                        final_scores.append(score[0])
                        print(score)
                        print(cek[0]['nama'], cek[0]['cc'],
                              cek[1]['nama'], cek[1]['cc'],
                              cek[2]['nama'], cek[2]['cc'],
                              cek[3]['nama'], cek[3]['cc'])
        print(final_scores)
        net.set_node_definition(name_node, final_scores)

# Menyimpan Bayesian Network ke dalam file
net.write_file("Data/fix_network.xdsl")
