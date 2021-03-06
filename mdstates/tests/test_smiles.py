from collections import Counter

import numpy as np
import pandas as pd

from ..smiles import (get_mol_dict, remove_common_molecules,
                      to_chemical_equation, find_reaction,
                      remove_consecutive_repeats, uniqueSMILES)


def test_get_mol_dict():
    smi = ['[Li]', 'O', 'O', 'CO']
    output = get_mol_dict(smi)

    for count, mol in output:
        ctr = 0
        for m in smi:
            if m == mol:
                ctr += 1
        assert count == ctr,\
            "Number of molecules not consistent for {}.".format(mol)
        assert mol in smi, "Molecule not found in original."

    smi2 = []
    try:
        get_mol_dict(smi2)
    except(Exception):
        pass
    else:
        raise Exception("Error not raised.")

    return


def test_remove_common_molecules():

    mol1 = ['O', 'C', 'C']
    mol2 = ['CO', 'C']

    diff_molecules = remove_common_molecules(mol1, mol2)
    assert 'O' in diff_molecules[0] and 'C' in diff_molecules[0],\
        "Incorrect molecules removed."
    assert 'CO' in diff_molecules[1], "Incorrect molecules removed."
    assert 'C' not in diff_molecules[1], "'C' should be removed."

    mol3 = ['O', 'C']
    mol4 = ['C', 'O']

    try:
        remove_common_molecules(mol3, mol4)
    except(Exception):
        pass
    else:
        raise Exception("Error not raised when molecule lists are equivalent.")

    return


def test_to_chemical_equation():
    mol_list1 = [(1, 'C#O'), (1, 'O=O')]
    mol_list2 = [(1, 'O=C=O'), (1, '[O]')]

    chem_eq = to_chemical_equation(mol_list1, mol_list2)

    assert chem_eq == "C#O + O=O --> O=C=O + [O]",\
        "Incorrect chemical equation."

    mol_list3 = [(1, ''), (1, '')]
    mol_list4 = [(1, ''), (1, '')]

    try:
        to_chemical_equation(mol_list3, mol_list4)
    except(Exception):
        pass
    else:
        raise Exception("Error is not raised for empty strings.")
    return


def test_find_reaction():
    smi1 = 'C.O=O.O=O'
    smi2 = 'O=C=O.O.O'
    eq = find_reaction(smi1, smi2)
    eq_list = eq.split(' --> ')
    assert eq_list[0] == 'C + 2 O=O' or eq_list[0] == '2 O=O + C',\
        "Reactants are wrong."
    assert eq_list[1] == 'O=C=O + 2 O' or eq_list[1] == '2 O + O=C=O',\
        "Products are wrong."
    return


def test_remove_consecutive_repeats():
    test_list = ['a', 'a', 'a', 'b', 'c', 'c', 'a']
    true_after = ['a', 'b', 'c', 'a']
    test_df = pd.DataFrame({'smiles': test_list,
                            'molecule': test_list,
                            'frame': list(range(len(test_list))),
                            'transition_frame': list(range(len(test_list)))})
    true_df_after = pd.DataFrame({'smiles': true_after,
                                  'molecule': true_after,
                                  'frame': [0, 3, 4, 6],
                                  'transition_frame': [0, 3, 4, 6]})
    test_df_after = remove_consecutive_repeats(test_df)
    for col in test_df_after:
        assert np.all(true_df_after[col] == test_df_after[col]),\
            "Lists not the same."
    return


def test_uniqueSMILES():
    test_list = ['a', 'a', 'a', 'b', 'c', 'c', 'a']

    true_after = Counter(['a', 'b', 'c'])
    test_after = Counter(uniqueSMILES(test_list))
    assert true_after == test_after, "Lists not the same."
    return
