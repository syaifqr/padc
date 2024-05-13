from flask import Flask, render_template, request, jsonify
import pysmile
import pysmile_license

app = Flask(__name__)

# Fungsi untuk mencetak posteriors dari satu node


def print_posteriors(net, node_handle):
    node_id = net.get_node_id(node_handle)
    childs_id = net.get_child_ids(node_handle)

    results = []
    if len(childs_id) > 0:
        if net.is_evidence(node_handle):
            # Jika node memiliki bukti, tambahkan informasi tentang bukti ke hasil
            result = (1.0,
                      f"{node_id} has evidence set ({net.get_evidence_id(node_handle)})")
        else:
            # Jika tidak ada bukti, tambahkan posteriors ke hasil
            posteriors = net.get_node_value(node_handle)
            result = []
            for i in range(0, len(posteriors)):
                outcome_id = net.get_outcome_id(node_handle, i)
                if outcome_id == 'present':
                    probability = posteriors[i]
                    result.append((probability,
                                  f"({node_id})={posteriors[i]}"))
    else:
        result = []  # Inisialisasi list kosong jika tidak ada child nodes

    return result

# Fungsi untuk mencetak posteriors dari semua node


def print_all_posteriors(net):
    results = []
    for handle in net.get_all_nodes():
        posteriors = print_posteriors(net, handle)
        # results.extend(print_posteriors(net, handle))
        if isinstance(posteriors, list):
            results.extend(posteriors)
    sorted_results = sorted(results, key=lambda x: x[0], reverse=True)
    return [result[1] for result in sorted_results if isinstance(result, tuple)]

# Fungsi untuk mengubah bukti dan memperbarui posteriors


def change_evidence_and_update(net, node_id, outcome_id):
    if outcome_id is not None:
        net.set_evidence(node_id, outcome_id)
    else:
        net.clear_evidence(node_id)
    net.update_beliefs()

# Route untuk halaman utama (berfungsi sebagai antarmuka web)


@app.route('/')
def index():
    return render_template('index.html')

# Route untuk pemrosesan gejala yang dipilih


@app.route('/process_symptoms', methods=['POST'])
def process_symptoms():
    # Inisialisasi jaringan dan membaca file network
    net = pysmile.Network()
    net.read_file("Data/fix_network.xdsl")

    # Mendapatkan data gejala yang dipilih dari permintaan POST
    data = request.get_json()
    selected_symptoms = data.get('symptoms', [])

    # Memproses setiap gejala yang dipilih
    for symptom in selected_symptoms:
        outcome_id = "present"  # Nilai bukti untuk gejala yang dipilih
        change_evidence_and_update(net, symptom, outcome_id)

    # Mendapatkan total posteriors setelah semua gejala diproses
    results = print_all_posteriors(net)

    # Mengembalikan hasil posteriors dalam format JSON
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True)
