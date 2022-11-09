#!/tools/python-3.9.2/bin/python

import numpy as np
import matplotlib.pyplot as plt
import argparse
import os.path


def main():
    # Variable for the format of your gnu files, spin unpolarized, spin up, spin down-change as needed:
    gnuformat = ['.bands.dat.gnu', '.spin1.dat.gnu', '.spin2.dat.gnu']
    # Format for the output file from band.x, spin unpolarized and spin up- change as needed:
    bnd_out_form = ['.bands.out', '.bands1.out']
    parser = argparse.ArgumentParser()
    parser.add_argument('-emin', '-ymin', type=float, default=-2.)
    parser.add_argument('-emax', '-ymax', type=float, default=2.)
    parser.add_argument('--scatter', action="store_true")
    parser.add_argument('--scattersize', '-s', type=float, default=2.)
    parser.add_argument('-fermi', type=float, default=-10000000.)
    parser.add_argument('-spinpol', action="store_true")
    parser.add_argument('-nscf', type=str, default='none')
    parser.add_argument("file", type=str)
    args = parser.parse_args()
    filebase = args.file.split('.')[0]
    fermi = fermi_check(filebase, args.fermi, args.nscf)
    if args.spinpol:
        gnufile = [filebase+gnuformat[1], filebase+gnuformat[2]]
        bnd_out = filebase + bnd_out_form[1]
    else:
        gnufile = filebase + gnuformat[0]
        bnd_out = filebase + bnd_out_form[0]


# Start of plotting
    if args.spinpol:
        bands1, x1 = read_data(gnufile[0], fermi)
        bands2, x2 = read_data(gnufile[1], fermi)
        x = x1
        if args.scatter:
            for b in bands2:
                plt.plot(x2, b, s=args.scatterize, color='r')
            for b in bands1:
                plt.plot(x1, b, s=args.scattersize, color='b')
        else:
            for b in bands2:
                plt.plot(x2, b, color='r')
            for b in bands1:
                plt.plot(x1, b, color='b')
    else:
        bands, x = read_data(gnufile, fermi)
        for b in bands:
            plt.plot(x, b, color='r')
    plt.xticks([0, x[-1]], [r'$\Gamma$', r'$\Gamma$'])
    plt.xlim([0, x[-1]])
    plt.ylim([args.emin, args.emax])
    plt.axhline(0, color='r', linestyle=":")
    if os.path.isfile(bnd_out):  # Use band.out file to identify high symmetry points
        sym = read_sym(bnd_out)
        for point in sym:
            if point != x[0] and point != x[-1]:
                plt.axvline(point, color='k', linestyle=":")
		else:
			print("The band.x output file "+bnd_out+" was not found. High symmetry points will not be plotted")
    plt.savefig(filebase + '.eps', dpi=600, format='eps', transparent=True)


def read_data(file, efermi):
    data = np.loadtxt(file, dtype=float)
    x = np.unique(data[:, 0])
    nks = len(x)
    nbands = int(len(data[:, 0]) / len(x))
    bands = np.zeros((nbands, nks))
    k_cnt = 0
    bnd_cnt = 0
    for line in data:
        if k_cnt == nks:
            k_cnt = 0
            bnd_cnt += 1
        bands[bnd_cnt, k_cnt] = line[1] - efermi
        k_cnt += 1
    return bands, x


def read_sym(file):
    with open(file) as file:
        sym = []
        for line in file:
            if "high-symmetry" in line:
                sym.append(float(line.split()[-1]))
    return sym


def fermi_check(filebase, fermi, nscf):
    if fermi == -10000000.:
        if nscf == "none":
            nscf = filebase+".nscf.out"
        if os.path.isfile(nscf):
            with open(nscf) as nscf:
                for line in nscf:
                    if 'the Fermi energy is' in line:
                        fermi = line.split()[4]
        else:
            print("The file "+nscf+" was not found in the current directory")
            exit("Specify the fermi energy or an nscf file")
    return float(fermi)


main()
