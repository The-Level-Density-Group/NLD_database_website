import numpy as np 
import math

def liquid_drop_mass(A,Z):
	N = A - Z
	M_n = 8.07144
	M_H = 7.28899

	c_1 = 15.677 * (1 - 1.79 * ((N - Z)/A)**2)
	E_vol = -c_1*A

	c_2 = 18.56 * (1 - 1.79 * ((N - Z)/A)**2)
	E_sur = c_2 * A**(2/3)

	E_coul = 0.717 * Z**2/A**(1/3) - 1.21129 * Z**2/A

	if N%2 == 0 and Z%2 == 0:
		delta_m = -11/np.sqrt(A)

	elif N%2 != 0 and Z%2 != 0:
		delta_m = 11/np.sqrt(A)

	else:
		delta_m = 0

	return M_n*N + M_H*Z + E_vol + E_sur + E_coul + delta_m


def bsfg_fitting(E, a, Delta):
    # Condition to handle low energies
    # a_tilde = 0.0722396*A + 0.195267 * A**(2/3) 
    # sigma = np.sqrt(0.01389 * A**(5/3)/a_tilde * np.sqrt(np.abs(E - Delta) * a))

    rho = (np.sqrt(np.pi) / 12) * (np.exp(2 * np.sqrt(a * (E - Delta))) / 
                          (a**0.25 * (E - Delta)**1.25))
    return rho


def ctm_fitting(x_data,T,E0):

    return 1/T * np.exp((x_data - E0)/T)
