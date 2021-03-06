from collections import Counter
# import shutil
import os

import mdtraj as md
import numpy as np
import networkx as nx
import pandas as pd
from rdkit import Chem

from ..core import Network
# from ..graphs import prepare_graph

currentdir = os.path.dirname(__file__)
testdir = os.path.join(currentdir, 'test_cases')
traj_path = os.path.join(testdir, 'test_case.xyz')
top_path = os.path.join(testdir, 'test_top.pdb')


def test_add_replica():
    net = Network()
    net.add_replica(traj_path, top_path)
    assert isinstance(net.replica[0]['traj'], md.Trajectory), \
        '"traj" is not of type: mdtraj.Trajectory'

    # Test assertion for trajectory file existence
    try:
        net.add_replica('bad_traj_file', top_path)
    except (Exception):
        pass
    else:
        raise Exception('Failed assertion',
                        'Bad trajectory file was accepted without error')

    # Test assertion for topology file existence
    try:
        net.add_replica(traj_path, 'bad_top_file')
    except (Exception):
        pass
    else:
        raise Exception('Failed assertion',
                        'Bad topology file was accepted without error')
    return


def test_remove_replica():
    net = Network()
    net.add_replica(traj_path, top_path)
    net.remove_replica(0)

    assert not net.replica, "Replica should be emtpy."

    try:
        net.remove_replica(0)
    except(IndexError):
        pass
    else:
        raise Exception("Bad index allowed.")

    return


def test_generate_contact_matrix():
    net = Network()
    net.add_replica(traj_path, top_path)
    net.generate_contact_matrix()

    assert np.all([x == 0 or x == 1 for x in
                   np.nditer(net.replica[0]['cmat'])])

    assert (net.replica[0]['cmat'][0, 1, :] == 1).all() and\
           (net.replica[0]['cmat'][0, 2, :] == 1).all() and\
           (net.replica[0]['cmat'][0, 3, :] == 1).all()

    n_frames = net.replica[0]['traj'].n_frames

    assert net.replica[0]['cmat'].shape ==\
        (net.n_atoms, net.n_atoms, n_frames)

    net = Network()
    net.add_replica(traj_path, top_path)
    net.generate_contact_matrix(ignore='Cl')

    assert (net.replica[0]['cmat'][[4, 5], :, :] == 0).all() and\
           (net.replica[0]['cmat'][:, [4, 5], :] == 0).all()

    net = Network()
    net.add_replica(traj_path, top_path)
    net.generate_contact_matrix(ignore=[4, 5])

    assert (net.replica[0]['cmat'][[4, 5], :, :] == 0).all() and\
           (net.replica[0]['cmat'][:, [4, 5], :] == 0).all()

    net = Network()
    net.add_replica(traj_path, top_path)
    net.generate_contact_matrix(ignore=[4, 'H'])

    assert (net.replica[0]['cmat'][4, :, :] == 0).all() and\
           (net.replica[0]['cmat'][:, 4, :] == 0).all() and\
           (net.replica[0]['cmat'][[1, 2, 3], :, :] == 0).all() and\
           (net.replica[0]['cmat'][:, [1, 2, 3], :] == 0).all(),\
        "Ignore feature is not working properly with lists."
    return


def test_generate_pairs():
    net = Network()
    net.add_replica(traj_path, top_path)

    net._generate_pairs()

    pairs = np.triu_indices(6, 1)

    for i, j in zip(*pairs):
        assert [i, j] in net._pairs

    return


def test_set_cutoff():
    net = Network()
    net.add_replica(traj_path, top_path)

    try:
        net.set_cutoff('CC', 0.2)
    except(TypeError):
        pass
    else:
        raise Exception("Non-list allowed.")

    try:
        net.set_cutoff(['C'], 0.2)
    except(ValueError):
        pass
    else:
        raise Exception("Single element allowed.")

    try:
        net.set_cutoff(['C', 'C', 'C'], 0.2)
    except(ValueError):
        pass
    else:
        raise Exception("Three atoms allowed.")

    try:
        net.set_cutoff(['C', 'C'], 0)
    except(ValueError):
        pass
    else:
        raise Exception("Zero cutoff allowed.")

    try:
        net.set_cutoff(['C', 'C'], -0.2)
    except(ValueError):
        pass
    else:
        raise Exception("Negative cutoff allowed.")

    net.set_cutoff(['Li', 'N'], 0.3)

    assert net._cutoff[frozenset(['Li', 'N'])] == 0.3

    return


def test_decode():
    net = Network()
    net.replica.append({'traj': None, 'cmat': None, 'path': None,
                        'processed': False, 'network': None})
    net.n_atoms = 3
    net.frames.append([])

    net.replica[0]['cmat'] = np.zeros((3, 3, 200), dtype=np.int32)
    net.replica[0]['cmat'][0, 1, :] = 1
    idx = np.arange(0, 200, 10)
    net.replica[0]['cmat'][0, 2, idx] = 1

    net.decode(use_python=True)

    assert np.all(net.replica[0]['cmat'][0, 1, :] == 1)
    assert np.all(net.replica[0]['cmat'][1, 2, :] == 0)
    assert np.all(net.replica[0]['cmat'][0, 2, :] == 0)

    # Now redo the tests without the Python Viterbi version
    net = Network()
    net.replica.append({'traj': None, 'cmat': None, 'path': None,
                        'processed': False, 'network': None})
    net.n_atoms = 3
    net.frames.append([])

    net.replica[0]['cmat'] = np.zeros((3, 3, 200), dtype=np.int32)
    net.replica[0]['cmat'][0, 1, :] = 1
    idx = np.arange(0, 200, 10)
    net.replica[0]['cmat'][0, 2, idx] = 1

    net.decode()

    assert np.all(net.replica[0]['cmat'][0, 1, :] == 1)
    assert np.all(net.replica[0]['cmat'][1, 2, :] == 0)
    assert np.all(net.replica[0]['cmat'][0, 2, :] == 0)

    return


def test_chemical_equations():
    net = Network()
    smiles_list = ['A.B.C', 'A.B.D', 'A.E.D']

    reactions = net.chemical_equations(-1, smiles_list)
    assert len(reactions) == 2, "List of equations not correct."

    assert reactions[0] == 'C --> D', "Incorrect first equation."
    assert reactions[1] == 'B --> E', "Incorrect second equation."

    return


def test_traj_to_topology():
    net1 = Network()
    net1.add_replica(traj_path, topology=top_path)
    table1, _ = net1.topology.top.to_dataframe()
    atoms1 = table1['element'].tolist()

    net2 = Network()
    net2.add_replica(traj_path)
    table2, _ = net2.topology.top.to_dataframe()
    atoms2 = table2['element'].tolist()

    assert atoms1 == atoms2, "Atom lists are not equivalent."

    new_top_name = os.path.join(testdir, 'test_case_topology.pdb')
    if os.path.exists(new_top_name):
        os.remove(new_top_name)
    return


def test_build_connections():
    net = Network()
    net.atoms = ['H', 'H']
    net.n_atoms = 2
    net.set_cutoff(['H', 'H'], 1.2)
    dist = np.array([[1.3], [1.0]])
    # dist = np.array([[[0, 1.3], [0, 0]], [[0, 1.0], [0, 0]]])
    dist = net._reshape_to_square(dist)
    cmat = net._build_connections(dist)
    assert cmat[0, 1, 0] == 0, "Nonbonded cutoff not working."
    assert cmat[0, 1, 1] == 1, "Bonded cutoff not working."
    return


def test_reshape_to_square():
    net = Network()
    net.n_atoms = 3
    linear = np.array([[1, 2, 3], [4, 5, 6]])
    square = net._reshape_to_square(linear)
    true = np.array([[[0, 0], [1, 4], [2, 5]],
                     [[0, 0], [0, 0], [3, 6]],
                     [[0, 0], [0, 0], [0, 0]]])
    assert np.all(square == true), "Not reshaping correctly."
    return


def test_get_atoms():
    net = Network()
    assert not net.atoms, "Atom list should be empty."
    net.add_replica(traj_path, top_path)
    true = Counter(['C', 'H', 'H', 'H', 'Cl', 'Cl'])
    test = Counter(net.atoms)
    assert true == test, "Incorrect atoms list."
    return


def test_build_network():
    true_net = nx.DiGraph()
    true_net.add_node('C', count=2, traj_count=1)
    true_net.add_node('O', count=1, traj_count=1)
    true_net.add_node('CC', count=1, traj_count=1)
    true_net.add_node('CCC', count=1, traj_count=1)
    true_net.add_edge('C', 'O', count=1, traj_count=1, frames=[6])
    true_net.add_edge('O', 'C', count=1, traj_count=1, frames=[11])
    true_net.add_edge('C', 'CC', count=1, traj_count=1, frames=[20])
    true_net.add_edge('CC', 'CCC', count=1, traj_count=1, frames=[34])

    test_df = pd.DataFrame({'smiles': ['C', 'O', 'C', 'CC', 'CCC'],
                            'molecule': [None for _ in range(5)],
                            'frame': [0, 6, 11, 20, 34],
                            'transition_frame': [0, 6, 11, 20, 34]})
    net = Network()
    net.replica.append({'structures': test_df})
    test_net = net._build_network(rep_id=0)
    # shutil.rmtree('SMILESimages')

    for node, data in true_net.nodes(data=True):
        assert node in test_net.nodes
        for d in data:
            assert data[d] == test_net.nodes[node][d]

    for u, v, data in true_net.edges(data=True):
        assert (u, v) in test_net.edges
        for d in data:
            assert data[d] == test_net.edges[(u, v)][d]
    return


def test_generate_SMILES():
    pass
    return


def test_draw_overall_network():
    pass
    return


def test_compute_distances():
    pass
    return


def test_build_cutoff():
    pass
    return


def test_bond_distance():
    pass
    return


def test_find_transition_frames():
    pass
    return


def test_compile_networks():
    pass
    return


def test_build_all_networks():
    pass
    return


def test_save():
    net = Network()
    net.add_replica(traj_path, top_path)
    net.generate_contact_matrix()
    net.decode()
    net.build_all_networks()
    net.save('test')
    if os.path.exists('test.txt'):
        os.remove('test.txt')
    else:
        raise AssertionError('Checkpont file not saved.')
    return


def test_load():
    CF_Cl = Chem.MolFromSmiles('CF.[Cl-]')
    CF_Cl = Chem.AddHs(CF_Cl)

    CCl_F = Chem.MolFromSmiles('CCl.[F-]')
    CCl_F = Chem.AddHs(CCl_F)

    net = Network()
    test_file = os.path.join(currentdir, 'test_cases', 'test_load.txt')
    net.load(test_file)
    true1 = pd.DataFrame({'smiles': ['CCl.[F-]', 'CF.[Cl-]', 'CCl.[F-]'],
                          'molecule': [CCl_F, CF_Cl, CCl_F],
                          'frame': [1, 100, 200],
                          'transition_frame': [1, 100, 200]})
    true2 = pd.DataFrame({'smiles': ['CCl.[F-]', 'CF.[Cl-]', 'CCl.[F-]'],
                          'molecule': [CCl_F, CF_Cl, CCl_F],
                          'frame': [1, 300, 500],
                          'transition_frame': [1, 300, 500]})
    true_dfs = [true1, true2]
    assert len(net.replica) == 2
    for rep, true_df in zip(net.replica, true_dfs):
        assert np.all(rep['structures']['smiles'] == true_df['smiles'])
        assert np.all(rep['structures']['transition_frame'] ==
                      true_df['transition_frame'])
        for rep_mol, true_mol in zip(rep['structures']['molecule'],
                                     true_df['molecule']):
            # Build list of atoms for both cases.
            test_atom_list = [atom.GetSymbol() for atom in
                              rep_mol.GetAtoms()]
            true_atom_list = [atom.GetSymbol() for atom in
                              true_mol.GetAtoms()]
            # Build counters for both cases from lists.
            test_counter = Counter(test_atom_list)
            true_counter = Counter(true_atom_list)
            assert test_counter == true_counter

    for i, rep in enumerate(net.replica):
        rep['network'] = net._build_network(i)

    # compiled = net._compile_networks()
    # net.network = compiled
    # final = prepare_graph(net.network, root_node=net._first_smiles)
    return
