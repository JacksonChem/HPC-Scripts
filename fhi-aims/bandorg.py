#!/usr/bin/env python
##!/tools/python-3.9.2/bin/python
"""
Script to plot or organize band structure and DOS files calculated with FHI-aims

This script can simply be called as just 'bandorg.py' to plot the bands in the current directory. This requires the
control.in, geometry.in, and bandYXXX.out files to be in the present directory.

Specifying a filename with '-f' or '--fileName' will assume your files are in the format: filename.ctrl
(for control.in), filename.geom (for geometry.in), and filename.bands (for the collated band file, see below). As in:
    bandorg.py --fileName filename.out
This will plot the band structure using the above files. The extension specified is not relevant as it will assume the
file name is specified as [filename].ext and remove everything after the first '.'

The collated band file can be automatically generated using the '-C' option as in:
  bandorg.py -C filename.out
which will collate all bandYXXX.out files in the current directory into the file filename.bands. Useful for organizing.

The filename.bands file can be expanded using:
    bandorg.py -E -f filename.out
which will reverse the collation into the individual bandYXXX.out files.

Plotting with bandorg.py:
The script will read through control.in/filename.ctrl to determine what will be plotted.

To specify the maximum and minimum energy range for the band plots use '-emax [float]' and '-emin [float]', defaults
used if omitted. Plotted energy values may be shifted using '-e_offset [float]', default of 0. Scatter plots for the
band structure (not currently implemented) can be obtained with '--Scatter', and "--scatterSize [float]" or
"-ss [float]" may be used to adjust the size of scatter points.

When plotting the band structure, if filename.bands exists the script will expand this file into a temporary directory
'./filename_tmp/' containing the individual bandYXXX.out files for plotting and delete the directory after.
Example:
    bandorg.py -emin -2.5 -emax 3.5 -f filename.out

Plotting density of states:
If 'output dos' and 'output species_proj_dos' are found in the control.in/filename.ctrl file, by default only the DOS
will be plotted. Plotting the atom_proj_dos isn't currently implemented.

To plot the projected density of states the '-s' or '--plot_species' option may be used which will plot
all species present in the control.in file in 1 image with separate graphs for each, alongside the band plot. To plot
all species together in one graph use the option '--plot_species_together' or '-st'.

For plotting the projected DOS with the lz component of each species separated out use '--show_lz' or '-lz'.
To specify the maximum and minimum energy x range of DOS and pDOS use '--dos_emax [float]' or '-dmin [float]' and
'--dos_emin [float]' '-dmin [float]', defaults will be used if omitted.
'--show_legend' or '-l' may be used to include a legend in the figure.
Example:
    bandorg.py -emin -2.5 -emax 3.5 -s -st --dos_emax 15.0 --dos_emin -15.0 -f filename.out (species project DOS)
    bandorg.py -emin -2.5 -emax 3.5 --dos_emax 15.0 --dos_emin -15.0 -f filename.out (non-projected DOS)

Use in job submission:
The flag '--IsJob' and '-J' can be used along with '--HomeDir' or '-D'  to specify the directory to save files to. If
called at the end of a calculation it will collate all bandYXXX.out files, if present, into filename.bands and if the
calculation is run in a separate directory e.g. a scratch directory it will copy the filename.bands file to the homedir
Example:
    bandorg.py --IsJob --HomeDir ~/path/to/dir -f filename.ctrl


  Written by Benjamin A Jackson, Auburn University
  baj0040@auburn.edu
"""

import os
import re
import shutil
import sys
import matplotlib
import numpy as np
matplotlib.use('PS')
import matplotlib.pyplot as plt
from matplotlib import gridspec
import argparse

matplotlib.pyplot.ioff()


def Main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--Collect', '-C', action="store_true")
    parser.add_argument('--Expand', '-E', action="store_true")
    parser.add_argument('-emin', type=float, default=-20.)
    parser.add_argument('-emax', type=float, default=5.)
    parser.add_argument('-e_offset', type=float, default=0.)
    parser.add_argument('--Scatter', action="store_true")
    parser.add_argument('--scatterSize', '-ss', type=float, default=2.)
    parser.add_argument('--fileName', '-f', type=str, default=None)
    parser.add_argument('--plot_species', '-s', action="store_true")
    parser.add_argument('--plot_species_together', '-st', action="store_true")
    parser.add_argument('--show_lz', '-lz', action="store_true")
    parser.add_argument('--show_legend', '-l', action="store_true")
    parser.add_argument('--dos_emax', '-dmax', type=float, default=-25.)
    parser.add_argument('--dos_emin', '-dmin', type=float, default=25.)
    parser.add_argument('--IsJob', '-J', action="store_true")
    parser.add_argument('--HomeDir', '-D', type=str)
    args = parser.parse_args()
    if args.Expand:  # Expands the .bands file that is collated by CollectBands
        file_list = FileChecker(args.fileName, checkIn_files=False)
        ExpandBands(file_list[0], False)
        sys.exit()
    if args.Collect:  # Collates bands files output by FHI-aims calculation into one text file
        file_baseName = FileChecker(args.fileName, checkIn_files=False)
        CollectBands(file_baseName)
        sys.exit()
    if args.IsJob:  # Flag used when the script is called as part of job submission
        file_list = FileChecker(args.fileName, False)
        for line in open('control.in'):  # Reads control.in to determine whether bands are being calculated
            words = line.split("#")[0].split()
            newline = " ".join(words)
            if newline.startswith("output band "):
                CollectBands(file_list[0].split('.')[0])
                shutil.copy(file_list[0].split('.')[0] + ".bands", args.HomeDir)
        sys.exit()
    if not args.IsJob:  # If not a job, then check for files, expand bands, and plot the bands
        if args.fileName is None:
            newDir = False
            bandDir = './'
            file_list = ["control.in", "geometry.in"]
        else:
            newDir = True
            file_list = FileChecker(args.fileName, checkIn_files=True)  # Check that files exist
            bandDir = ExpandBands(file_list[0], newDir)  # New dir, expand .bands file into separate files
        BandPlot(file_list, bandDir, args.emin, args.emax, args.e_offset, args.Scatter, args.scatterSize,
                 args.plot_species, args.plot_species_together, args.dos_emax, args.dos_emin)
        if newDir:
            shutil.rmtree(bandDir)  # Remove created directory and band files after completion


def CollectBands(file_baseName):
    """This function will collate all bandYXXX.out files into a single text file to simplify"""
    bandFiles = [f for f in os.listdir(os.getcwd()) if re.match('band[0-9]+\.out', f)]
    with open(os.path.join(os.getcwd(), file_baseName + '.bands'), 'w') as collection:
        for fileName in bandFiles:
            collection.write(fileName + '\n')
            with open(os.path.join('.', fileName), 'r') as file:
                for line in file:
                    collection.write(line)


def ExpandBands(fileName, newDir):
    """This function will expand the collated band files for plotting"""
    currDir = os.getcwd()
    file_baseName = fileName.split('.')[0]
    if newDir:
        try:
            bandDir = os.path.join(currDir, file_baseName + '_tmp')
            os.mkdir(os.path.join(bandDir))
        except OSError as error:
            exit(
                "The temp band dir " + bandDir + " already exists. Please remove from the current directory to proceed")
    if not newDir:
        bandDir = currDir
    with open(file_baseName + '.bands', 'r') as collection:
        fileLines = []
        for line in collection:
            fileLines.append(line)
        i = 0
        while i <= (len(fileLines) - 1):
            if match := re.search('band[0-9]+\.out', fileLines[i]):
                fileName = match.group(0)
                i = i + 1
            else:
                with open(os.path.join(bandDir, fileName), 'w') as file:
                    while i <= (len(fileLines) - 1):  # True :
                        if match := re.search('band[0-9]+\.out', fileLines[i]):
                            break
                        file.write(fileLines[i])
                        i = i + 1
    return bandDir


def FileChecker(fileName, checkIn_files):
    file_baseName = fileName.split('.')[0]
    if checkIn_files:
        try:
            if os.path.exists(os.path.join(os.getcwd(), file_baseName + '.ctrl')) is False:
                raise FileNotFoundError
        except FileNotFoundError:
            exit(file_baseName + ".ctrl was not found in the current directory.")
            try:
                if os.path.exists(os.path.join(os.getcwd(), file_baseName + '.geom')) is False:
                    raise FileNotFoundError
            except FileNotFoundError:
                exit(file_baseName + ".geom was not found in the current directory.")

            try:
                if os.path.exists(os.path.join(os.getcwd(), file_baseName + '.bands')) is False:
                    raise FileNotFoundError
            except FileNotFoundError:
                exit(file_baseName + ".bands was not found in the current directory.")
        if not checkIn_files:
            pass
    fileList = [file_baseName + '.ctrl', file_baseName + '.geom']
    return fileList


def BandPlot(file_list, bandDir, ylim_lower, ylim_upper,
             energy_offset, scatterOption, scatterSize, PLOT_SPECIES, PLOT_SPECIES_TOGETHER, dos_emin, dos_emax):
    plot_ext = ".eps"  # file type extension used in the exported figure
    print_resolution = 250  # The DPI used for printing out images
    default_line_width = 1  # Change the line width of plotted bands and k-vectors, 1 is default
    font_size = 12  # Change the font size.  12 is the default.
    SHOW_LEGEND = False
    SHOW_L_COMPONENT = False
    PLOT_BANDS = False
    PLOT_DOS = False
    PLOT_DOS_TETRAHEDRON = False
    PLOT_DOS_SPECIES = False
    PLOT_DOS_SPECIES_TETRAHEDRON = False
    PLOT_DOS_ATOM = False
    PLOT_DOS_ATOM_TETRAHEDRON = False
    PLOT_DOS_REVERSED = False
    PLOT_SOC = False
    if PLOT_SPECIES:
        PLOT_ONLY_DOS = False
        PLOT_ONLY_SPECIES = True
    else:
        PLOT_ONLY_DOS = True
        PLOT_ONLY_SPECIES = False

    file_name_ctrl = file_list[0]
    file_name_geom = file_list[1]
    latvec = []
    # Read geometry.in file for lattice vectors
    for line in open(file_name_geom):
        line = line.split("#")[0]
        words = line.split()
        if len(words) == 0:
            continue
        if words[0] == "lattice_vector":
            if len(words) != 4:
                raise Exception(file_name_geom + ": Syntax error in line '" + line + "'")
            latvec += [np.array(list(map(float, words[1:4])))]
        if len(latvec) == 3:
            break
    if len(latvec) != 3:
        raise Exception(file_name_geom + ": Must contain exactly 3 lattice vectors")
    # Determine reciprocal lattice vectors
    latvec = np.asarray(latvec)
    rlatvec = []
    volume = (np.dot(latvec[0, :], np.cross(latvec[1, :], latvec[2, :])))
    rlatvec.append(np.array(2 * np.pi * np.cross(latvec[1, :], latvec[2, :]) / volume))
    rlatvec.append(np.array(2 * np.pi * np.cross(latvec[2, :], latvec[0, :]) / volume))
    rlatvec.append(np.array(2 * np.pi * np.cross(latvec[0, :], latvec[1, :]) / volume))
    rlatvec = np.asarray(rlatvec)
    # Interpret input files and determine types of plots
    species_list = []
    max_spin_channel = 1
    band_segments = []
    band_totlength = 0.0  # total length of all band segments
    for line in open(file_name_ctrl):
        words = line.split("#")[0].split()  # List of words in line,
        nline = " ".join(words)  # What is join doing?
        if nline.startswith("output band "):  # Read band lines
            if len(words) < 9 or len(words) > 11:  # 9 for end and start xyz, 11 for names of end and start
                raise Exception(file_name_ctrl + ": Syntax error in line '" + line + "'")
            PLOT_BANDS = True
            start = np.array(list(map(float, words[2:5])))  # Get x y z of start
            end = np.array(list(map(float, words[5:8])))  # Get x y z of end
            length = np.linalg.norm(np.dot(rlatvec, end) - np.dot(rlatvec, start))  # Get length of k-path
            band_totlength += length
            npoint = int(words[8])  # Number of points for that band
            startname = ""
            endname = ""
            if len(words) > 9:
                startname = words[9]  # Name of point
            if len(words) > 10:  # Name of end
                endname = words[10]
            band_segments += [(start, end, length, npoint, startname, endname)]
        elif nline.startswith("spin collinear") and not PLOT_SOC:
            max_spin_channel = 2
        elif nline.startswith("calculate_perturbative_soc") or nline.startswith("include_spin_orbit") \
                or nline.startswith("include_spin_orbit_sc"):
            PLOT_SOC = True
            max_spin_channel = 1
        elif nline.startswith("output dos "):
            PLOT_DOS = True
        elif nline.startswith("output dos_tetrahedron"):
            PLOT_DOS_TETRAHEDRON = True
        elif nline.startswith("output species_proj_dos "):
            PLOT_DOS_SPECIES = True
        elif nline.startswith("output species_proj_dos_tetrahedron"):
            PLOT_DOS_SPECIES_TETRAHEDRON = True
        elif nline.startswith("output atom_proj_dos "):
            PLOT_DOS_ATOM = True
        elif nline.startswith("output atom_proj_dos_tetrahedron"):
            PLOT_DOS_ATOM_TETRAHEDRON = True
        elif nline.startswith("species"):
            if len(words) != 2:
                raise Exception("control.in: Syntax error in line '" + line + "'")
            species_list += [words[1]]
    if PLOT_BANDS:
        if (PLOT_DOS_SPECIES or PLOT_DOS_SPECIES_TETRAHEDRON) and not PLOT_ONLY_DOS:
            if PLOT_SPECIES_TOGETHER:
                fig, axs = plt.subplots(1, 2, sharey='row')
                ax_bands = axs[0]
                species_dos = axs[1]
            else:
                width_array = [1] * (len(species_list) + 1)
                width_array[0] = 3
                fig, axs = plt.subplots(1, len(species_list) + 1, sharey='row', gridspec_kw={'width_ratios': width_array
                                                                                             })
                ax_bands = axs[0]
        elif PLOT_DOS or PLOT_DOS_TETRAHEDRON:
            fig, axs = plt.subplots(1, 2, sharey='row')
            ax_bands = axs[0]
            ax_dos = axs[1]
        else:
            ax_bands = plt.subplot(1, 1, 1)
            ax_bands.set(ylabel='E [eV]')
    #  Plotting the band structure
    if PLOT_BANDS:
        ax_bands.axhline(0, color='k', linestyle=":")
        iband = 0
        xpos = 0.
        labels = [(0.0, band_segments[0][4])]
        for start, end, length, npoint, startname, endname in band_segments:
            iband += 1
            xvals = xpos + np.linspace(0, length, npoint)
            xpos = xvals[-1]
            labels += [(xpos, endname)]
            for spin in range(1, max_spin_channel + 1):
                fname = bandDir + "/band%i%03i.out" % (spin, iband)
                idx = []
                kvec = []
                band_energies = []
                band_occupations = []
                for line in open(fname):
                    words = line.split()
                    idx += [int(words[0])]
                    kvec += [list(map(float, words[1:4]))]
                    band_occupations += [list(map(float, words[4::2]))]
                    band_energies += [list(map(float, words[5::2]))]
                    band_energies[-1] = [x - energy_offset for x in band_energies[-1]]
                band_energies = np.asarray(band_energies)
                for b in range(band_energies.shape[1]):
                    #ax_bands.plot(xvals, band_energies[:, b], color=' br'[spin], linestyle=["","solid", "dashed"][spin])
                    ax_bands.plot(xvals, band_energies[:, b], color=' br'[spin])
        tickx = []
        tickl = []
        for xpos, l in labels:
            ax_bands.axvline(xpos, color='k', linestyle=":")
            tickx += [xpos]
            if len(l) > 1:
                if l == "Gamma":
                    l = "$\\" + l + "$"
            tickl += [l]
        ax_bands.set_xlim(labels[0][0], labels[-1][0])
        ax_bands.set_xticks(tickx)
        ax_bands.set_xticklabels(tickl)
        ax_bands.set_ylim(ylim_lower, ylim_upper)
    if max_spin_channel == 2:
        spinstrs = ["_spin_up", "_spin_down"]
        spinsgn = [1., -1.]
    else:
        spinstrs = [""]
        spinsgn = [1.]
    #  Plotting the projected density of states
    if (PLOT_DOS_SPECIES or PLOT_DOS_SPECIES_TETRAHEDRON) and not PLOT_ONLY_DOS:
        species_energy = []
        tdos = []
        lz_dos = []
        for species in species_list:
            val_atom = []
            for spin in spinstrs:
                if PLOT_DOS_SPECIES:
                    file = open(species + "_l_proj_dos" + spin + ".dat")
                else:
                    file = open(species + "_l_proj_dos" + spin + "_tetrahedron.dat")
                file.readline()
                file.readline()
                mu = float(file.readline().split()[-2])
                file.readline()
                val_spin = []
                for line in file:
                    val_spin += [list(map(float, line.split()))]
                val_atom += [val_spin]
            val_atom = np.asarray(val_atom).transpose(1, 0, 2)
            species_energy += [val_atom[:, :, 0] - energy_offset]
            tdos += [np.asarray(val_atom[:, :, 1])]
            lz_dos += [np.asarray(val_atom[:, :, 2:])]
        if PLOT_SPECIES_TOGETHER:
            for i in range(len(species_list)):
                for ispin in range(max_spin_channel):
                    if SHOW_L_COMPONENT:
                        for lz in range(lz_dos[i].shape[2]):
                            species_dos.plot(lz_dos[i][:, ispin, lz] * spinsgn[ispin], species_energy[i][:, ispin],
                                             linestyle=["solid", "dashed"][ispin],
                                             label='%s (l=%i) %s' % (species_list[i], lz, ['up', 'down'][ispin]))
                    else:
                        species_dos.plot(tdos[i][:, ispin] * spinsgn[ispin], species_energy[i][:, ispin],
                                         linestyle=["solid", "dashed"][ispin],
                                         label='%s %s' % (species_list[i], ['up', 'down'][ispin]))
        else:
            for i in range(len(species_list)):
                for ispin in range(max_spin_channel):
                    if SHOW_L_COMPONENT:
                        for lz in range(lz_dos[i].shape[2]):
                            axs[i + 1].plot(lz_dos[i][:, ispin, lz] * spinsgn[ispin], species_energy[i][:, ispin],
                                            linestyle=["solid", "dashed"][ispin],
                                            label='%s (l=%i) %s' % (species_list[i], lz, ['up', 'down'][ispin]))
                    else:
                        axs[i + 1].plot(tdos[i][:, ispin] * spinsgn[ispin], species_energy[i][:, ispin], linestyle='-',
                                        label='%s %s' % (species_list[i], ['up', 'down'][ispin]), color='br'[ispin])
                axs[i + 1].set_title(species_list[i])
                axs[i + 1].set_xlim(dos_emin, dos_emax)
                axs[i + 1].axvline(0, color='k', ls=':')
                axs[i + 1].axhline(0, color='k', ls=':')
    #  Plotting the non-projected density of states
    if (PLOT_DOS or PLOT_DOS_TETRAHEDRON) and not PLOT_ONLY_SPECIES:
        energy = []
        dos = []
        if PLOT_DOS:
            f = open("KS_DOS_total.dat")
        else:
            f = open("KS_DOS_total_tetrahedron.dat")
        f.readline()
        mu = float(f.readline().split()[-2])
        f.readline()
        if max_spin_channel == 1:
            for line in f:
                if not line.startswith('#'):
                    e, d = line.split()
                    energy += [float(e)]
                    energy[-1] = energy[-1] - energy_offset
                    dos += [(1 * float(d),)]
        else:
            for line in f:
                if not line.startswith('#'):
                    e, d1, d2 = line.split()
                    energy += [float(e)]
                    energy[-1] = energy[-1] - energy_offset  # Apply energy offset if specified to all DOS energies
                    dos += [(float(d1), float(d2))]
        energy = np.asarray(energy)
        dos = np.asarray(dos)
        for ispin in range(max_spin_channel):
            ax_dos.plot(dos[:, ispin] * spinsgn[ispin], energy, color='br'[ispin])
        ax_dos.set_xlim(dos_emin, dos_emax)
        ax_dos.axvline(0, color='k', ls=':')
        ax_dos.axhline(0, color='k', ls=':')
    ####################################################################################################################
    matplotlib.rcParams['lines.linewidth'] = default_line_width
    matplotlib.rcParams['savefig.dpi'] = print_resolution
    matplotlib.rcParams['font.size'] = font_size
    if file_name_ctrl == "control.in":
        plot_filename = "aimsplot" + plot_ext
    else:
        plot_filename = file_name_ctrl.split('.')[0] + plot_ext
    plt.savefig(plot_filename, transparent=True)


Main()
