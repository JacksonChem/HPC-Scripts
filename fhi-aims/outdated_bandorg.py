#!/tools/python-3.9.2/bin/python

import os
import re
import shutil
import sys
import numpy as np
import matplotlib
matplotlib.use('PS')
import matplotlib.pyplot as plt
import argparse
import glob
matplotlib.pyplot.ioff()

def Main() :
	parser = argparse.ArgumentParser()
	parser.add_argument('--IsJob', '-J', action="store_true")
	parser.add_argument('--HomeDir', '-D', type=str)
	parser.add_argument('--Collect', '-C', action="store_true")
	parser.add_argument('--Expand', '-E', action="store_true")
	parser.add_argument('-emin', '-ymin', type=float, default=-100000000.)
	parser.add_argument('-emax', '-ymax', type=float, default=-100000000.)
	parser.add_argument('--Scatter', action="store_true")
	parser.add_argument('--scatterSize', '-s', type=float, default=2.)
	parser.add_argument('-e_offset', type=float, default=0.)
	parser.add_argument("fileName", type=str)
	args=parser.parse_args()
	if args.Expand :
		file_baseName = FileChecker(args.fileName,checkIn_files=False)
		ExpandBands(file_baseName,newDir=False)
		sys.exit()
	if args.Collect :
		file_baseName = FileChecker(args.fileName,checkIn_files=False)
		CollectBands(file_baseName)
		sys.exit()
	if args.IsJob :
		file_baseName = FileChecker(args.fileName,0)
		for line in open('control.in') :
			words = line.split("#")[0].split()
			newline = " ".join(words)
			if newline.startswith("output band ") : 
				CollectBands(file_baseName) 
				shutil.copy(file_baseName+".bands", args.HomeDir)
			#if newline.startswith("output cube ") :
			#	cubeFile=[f for f in os.listdir(os.getcwd()) if re.match('band[0-9]+\.out',f)]
			#	shutil.move(cubeFile[0],os.path.join(args.HomeDir,file_baseName+'.cube'))
		sys.exit()
	if not args.IsJob :
		file_baseName = FileChecker(args.fileName,checkIn_files=True) #Check that files exist, 1 confirms .ctrl and .geom
		bandDir=ExpandBands(file_baseName,newDir=True) #Create a new directory and expand band collect file into seperate files
		BandPlot(file_baseName, bandDir, args.emin, args.emax, args.e_offset,args.Scatter,args.scatterSize) #Create plots based on input file settings
		CleanUpExpansion(bandDir) #Remove created directory and band files after completion
#==================================================#
#This function will collect all bands into a single file to simplify
def CollectBands(file_baseName) :
	bandFiles=[f for f in os.listdir(os.getcwd()) if re.match('band[0-9]+\.out',f)] #Change to SCRDIR
	with open(os.path.join(os.getcwd(),file_baseName+'.bands'), 'w') as collection :
		for fileName in bandFiles :
			collection.write(fileName + '\n')
			with open(os.path.join('.',fileName), 'r') as file :
				for line in file :
					collection.write(line)
#==================================================#
#This function will expand the collected bands file for plotting
def ExpandBands(file_baseName,newDir) :
	currDir = os.getcwd()
	if newDir :
		try :
			bandDir=os.path.join(currDir, file_baseName+'_tmp')
			os.mkdir(os.path.join(bandDir))
		except OSError as error :
			exit("The temp band dir "+bandDir+" already exists. Please remove from the current directory to proceed")
			#Add a variable to track if the above folder currently exists
		shutil.copy(file_baseName+".ctrl", bandDir)
		shutil.copy(file_baseName+".geom", bandDir)
	if not newDir :
		bandDir=currDir
	#with open(os.path.join(currDir, file_baseName+'.bands'), 'r') as collection :
	with open(file_baseName+'.bands', 'r') as collection :
		fileLines = []
		for line in collection :
			fileLines.append(line)
		i = 0
		while i <= (len(fileLines) -1) :
			if match := re.search('band[0-9]+\.out',fileLines[i]) :
				fileName = match.group(0)
				i = i+1
			else :
				with open(os.path.join(bandDir, fileName ), 'w') as file :
					while i <= (len(fileLines) -1) : #True : 
						if match := re.search('band[0-9]+\.out',fileLines[i]) :
							break
						file.write(fileLines[i])
						i = i+1
	return(bandDir)
#==================================================#
def CleanUpExpansion(bandDir) :
	shutil.rmtree(bandDir)
#==================================================#
def FileChecker(fileName,checkIn_files) :
	file_baseName = fileName.split('.')[0]
	if checkIn_files :	
		try :
			if os.path.exists(os.path.join(os.getcwd(), file_baseName+'.ctrl')) is False :
				raise FileNotFoundError
		except FileNotFoundError :
			exit(file_baseName+".ctrl was not found in the current directory.")
			try :
				if os.path.exists(os.path.join(os.getcwd(), file_baseName+'.geom')) is False :
					raise FileNotFoundError
			except FileNotFoundError :
				exit(file_baseName+".geom was not found in the current directory.")

			try :
				if os.path.exists(os.path.join(os.getcwd(), file_baseName+'.bands')) is False :
					raise FileNotFoundError
			except FileNotFoundError :
				exit(file_baseName+".bands was not found in the current directory.")
		if not checkIn_files :
			pass

	return(file_baseName)
#=======================================#
#The following function comes from the FHI-AIMS aimsplot.py and has been editted to work here
def BandPlot(file_baseName,bandDir,ylim_lower,ylim_upper,
             energy_offset,scatterOption,scatterSize) :
	#os.chdir(os.path.join(currDir, 'tmpbandfolder'))
	print_resolution = 250	# The DPI used for printing out images
	default_line_width = 1	# Change the line width of plotted bands and k-vectors, 1 is default
	font_size = 12			# Change the font size.  12 is the default.
	should_spline = False	# Turn on spline interpolation for band structures NOT VERY WELL TESTED!
	output_x_axis = True	# Whether to output the x-axis (e.g. the e=0 line) or not
	spline_factor = 10		# If spline interpolation turned on, the sampling factor (1 is the original grid)
	maxdos_output = -1		# The maximum value of the DOS axis (a.k.a. x-axis) in the DOS
							# For zero or negative values, the script will use its default value, the maximum
							# value for the DOS in the energy window read in
	FERMI_OFFSET = False
	PLOT_BANDS = False
	PLOT_DOS = False
	PLOT_DOS_TETRAHEDRON = False
	PLOT_DOS_SPECIES = False
	PLOT_DOS_SPECIES_TETRAHEDRON = False
	PLOT_DOS_ATOM = False
	PLOT_DOS_ATOM_TETRAHEDRON = False
	PLOT_SOC = False # This is needed because there will only be one "spin" channel output,
					 # but collinear spin may (or may not) be turned on, so the "spin
					 # collinear" setting needs to be overridden
	PLOT_DOS_REVERSED = False
#	if options.no_legend:
#	   SHOW_LEGEND = False
#	else:
#	   SHOW_LEGEND = True
	if ylim_lower == -100000000. and ylim_upper == -100000000.:
		CUSTOM_YLIM = False
		ylim_lower = -20.
		ylim_upper = 5.
	else:
		CUSTOM_YLIM = True
	if energy_offset != 0.:
		FERMI_OFFSET = True
	latvec = []
	for line in open(file_baseName+".geom"):
		line = line.split("#")[0]
		words = line.split()
		if len(words) == 0:
			continue
		if words[0] == "lattice_vector":
			if len(words) != 4:
				raise Exception(file_baseName+".geom: Syntax error in line '"+line+"'")
			latvec += [ np.array(list(map(float,words[1:4]))) ]
	if len(latvec) != 3:
		raise Exception(file_baseName+".geom: Must contain exactly 3 lattice vectors")
	latvec = np.asarray(latvec)
#Calculate reciprocal lattice vectors
	rlatvec = []
	volume = (np.dot(latvec[0,:],np.cross(latvec[1,:],latvec[2,:])))
	rlatvec.append(np.array(2*np.pi*np.cross(latvec[1,:],latvec[2,:])/volume))
	rlatvec.append(np.array(2*np.pi*np.cross(latvec[2,:],latvec[0,:])/volume))
	rlatvec.append(np.array(2*np.pi*np.cross(latvec[0,:],latvec[1,:])/volume))
	rlatvec = np.asarray(rlatvec)
########################
#Interpret input files and determine types of plots
	species = []
	max_spin_channel = 1
	band_segments = []
	band_totlength = 0.0 # total length of all band segments
	for line in open(file_baseName+".ctrl"):
		words = line.split("#")[0].split()
		nline = " ".join(words)
		if nline.startswith("spin collinear") and not PLOT_SOC:
			max_spin_channel = 2
		if nline.startswith("calculate_perturbative_soc") or nline.startswith("include_spin_orbit") or nline.startswith("include_spin_orbit_sc"):
			PLOT_SOC = True
			max_spin_channel = 1
		if nline.startswith("output band "):
			if len(words) < 9 or len(words) > 11:
				raise Exception(file_baseName+".ctrl: Syntax error in line '"+line+"'")
			PLOT_BANDS = True
			start = np.array(list(map(float,words[2:5])))
			end = np.array(list(map(float,words[5:8])))
			length = np.linalg.norm(np.dot(rlatvec,end) - np.dot(rlatvec,start))
			band_totlength += length
			npoint = int(words[8])
			startname = ""
			endname = ""
			if len(words)>9:
				startname = words[9]
			if len(words)>10:
				endname = words[10]
			band_segments += [ (start,end,length,npoint,startname,endname) ]
		if nline.startswith("output dos "):
			PLOT_DOS = True
		if nline.startswith("output dos_tetrahedron"):
			PLOT_DOS_TETRAHEDRON = True
		if nline.startswith("output species_proj_dos "):
			PLOT_DOS_SPECIES = True
		if nline.startswith("output species_proj_dos_tetrahedron"):
			PLOT_DOS_SPECIES_TETRAHEDRON = True
		if nline.startswith("output atom_proj_dos "):
			PLOT_DOS_ATOM = True
		if nline.startswith("output atom_proj_dos_tetrahedron"):
			PLOT_DOS_ATOM_TETRAHEDRON = True
		if nline.startswith("species"):
			if len(words) != 2:
				raise Exception(file_baseName+".ctrl: Syntax error in line '"+line+"'")
			species += [ words[1] ]
#######################
	if PLOT_SOC:
		max_spin_channel = 1
	if PLOT_BANDS and (PLOT_DOS or PLOT_DOS_TETRAHEDRON or PLOT_DOS_SPECIES or PLOT_DOS_SPECIES_TETRAHEDRON):
		ax_bands = plt.axes([0.1,0.1,0.6,0.8])
		ax_dos = plt.axes([0.72,0.1,0.18,0.8],sharey=ax_bands)
		ax_dos.set_title("DOS")
		plt.setp(ax_dos.get_yticklabels(),visible=False)
		ax_bands.set_ylabel("E [eV]")
		PLOT_DOS_REVERSED = True
	elif PLOT_BANDS:
		ax_bands = plt.subplot(1,1,1)
	elif PLOT_DOS or PLOT_DOS_TETRAHEDRON or PLOT_DOS_SPECIES or PLOT_DOS_SPECIES_TETRAHEDRON:
		ax_dos = plt.subplot(1,1,1)
		ax_dos.set_title("DOS")
		PLOT_DOS_REVERSED = False
#######################
	if PLOT_BANDS:
		if output_x_axis:
			ax_bands.axhline(0,color=(1.,0.,0.),linestyle=":")
		prev_end = band_segments[0][0]
		distance = band_totlength / 30.0 # distance between line segments that do not coincide
		iband = 0
		xpos = 0.0
		labels = [ (0.0,band_segments[0][4]) ]
		for start,end,length,npoint,startname,endname in band_segments:
			iband += 1
			if any(start != prev_end):
				xpos += distance
				labels += [ (xpos,startname) ]
			xvals = xpos+np.linspace(0,length,npoint)
			xpos = xvals[-1]
			labels += [ (xpos,endname) ]
			prev_end = end
			prev_endname = endname
			for spin in range(1,max_spin_channel+1):
				#fname = "band%i%03i.out"%(spin,iband)
				fname = bandDir+"/band%i%03i.out"%(spin,iband)
				idx = []
				kvec = []
				band_energies = []
				band_occupations = []
				for line in open(fname):
					words = line.split()
					idx += [ int(words[0]) ]
					kvec += [ list(map(float,words[1:4])) ]
					band_occupations += [ list(map(float,words[4::2])) ]
					band_energies += [ list(map(float,words[5::2])) ]
					# Apply energy offset if specified to all band energies just read in
					band_energies[-1] = [x - energy_offset for x in band_energies[-1]]
				assert(npoint) == len(idx)
				band_energies = np.asarray(band_energies)
				for b in range(band_energies.shape[1]):
					if scatterOption :
						ax_bands.scatter(xvals,band_energies[:,b],color=' br'[spin],s=scatterSize)
					else :
						ax_bands.plot(xvals,band_energies[:,b],color=' br'[spin])
		tickx = []
		tickl = []
		for xpos,l in labels:
			ax_bands.axvline(xpos,color='k',linestyle=":")
			tickx += [ xpos ]
			if len(l)>1:
				if l=="Gamma":
					 l = "$\\"+l+"$"
			tickl += [ l ]
#		for x, l in zip(tickx, tickl):
#			print("| %8.3f %s" % (x, repr(l)))
		ax_bands.set_xlim(labels[0][0],labels[-1][0])
		ax_bands.set_xticks(tickx)
		ax_bands.set_xticklabels(tickl)
#######################
#None of this section is editted to fully work with my new format
	if PLOT_DOS or PLOT_DOS_TETRAHEDRON or PLOT_DOS_SPECIES or PLOT_DOS_SPECIES_TETRAHEDRON:
		pass
	else:
		ax_bands.set_ylim(ylim_lower,ylim_upper) # just some random default -- definitely better than the full range including core bands
	if PLOT_DOS_SPECIES or PLOT_DOS_SPECIES_TETRAHEDRON:
		spinstrs = [ "" ]
		if max_spin_channel == 2:
			spinstrs = [ "_spin_up","_spin_dn" ]
		species_energy = []
		tdos = []
		ldos = []
		maxdos = 0.0
		for s in species:
			val_s = []
			for ss in spinstrs:
				if PLOT_DOS_SPECIES:
					f = open(s+"_l_proj_dos"+ss+".dat")
				else:
					f = open(s+"_l_proj_dos"+ss+"_tetrahedron.dat")
				f.readline()
				f.readline()
				mu = float(f.readline().split()[-2])
				f.readline()
				val_ss = []
				for line in f:
					val_ss += [ list(map(float,line.split())) ]
				val_s += [ val_ss ]
			val_s = np.asarray(val_s).transpose(1,0,2)
			# Here val_s is a NumPy data structures, so to apply offset
			# we don't need to use list comprehension
			species_energy += [ val_s[:,:,0] - energy_offset ]
			tdos += [ np.asarray(val_s[:,:,1]) ] #I have altered these to get rid of the smoothdos function
			ldos += [ np.asarray(val_s[:,:,2:]) ] #This change is not yet tested
			#tdos += [ smoothdos(val_s[:,:,1]) ]
			#ldos += [ smoothdos(val_s[:,:,2:]) ]
			maxdos = max(maxdos,tdos[-1].max())
		for e in species_energy:
			for i in range(e.shape[1]):
				assert all(e[:,i] == species_energy[0][:,0])
		species_energy = species_energy[0][:,0]

	if PLOT_DOS or PLOT_DOS_TETRAHEDRON:
		if PLOT_DOS:
			f = open("KS_DOS_total.dat")
		else:
			f = open("KS_DOS_total_tetrahedron.dat")
		f.readline()
		mu = float(f.readline().split()[-2])
		f.readline()
		energy = []
		dos = []
		if max_spin_channel == 1:
			for line in f:
				if not line.startswith('#'):
					e,d = line.split()
					energy += [ float(e) ]
					energy[-1] = energy[-1] - energy_offset
					dos += [ (1*float(d),) ]
		else:
			for line in f:
				if not line.startswith('#'):
					e,d1,d2 = line.split()
					energy += [ float(e) ]
					# Apply energy offset if specified to all DOS energies just read in
					energy[-1] = energy[-1] - energy_offset
					dos += [ (float(d1),float(d2)) ]
		energy = np.asarray(energy)
		#dos = smoothdos(dos) 
		dos = np.asarray(dos) #Also removed smoothdos here
		maxdos = dos.max()
		spinsgn = [ 1. ]
		if max_spin_channel == 2:
			spinsgn = [ 1.,-1. ]
		if PLOT_DOS_REVERSED:
			ax_dos.axhline(0,color='k',ls='--')
			ax_dos.axvline(0,color=(0.5,0.5,0.5))
			if PLOT_DOS_SPECIES or PLOT_DOS_SPECIES_TETRAHEDRON:
				for sp in range(len(species)):
					for ispin in range(max_spin_channel):
						ax_dos.plot(tdos[sp][:,ispin]*spinsgn[ispin],species_energy,linestyle='-',label='%s %s'%(species[sp],['up','down'][ispin]))
						if SHOW_L:
							for l in range(ldos[sp].shape[2]):
								ax_dos.plot(ldos[sp][:,ispin,l]*spinsgn[ispin],species_energy,linestyle='--',label='%s (l=%i) %s'%(species[sp],l,['up','down'][ispin]))

			if PLOT_DOS or PLOT_DOS_TETRAHEDRON:
				for ispin in range(max_spin_channel):
					ax_dos.plot(dos[:,ispin]*spinsgn[ispin],energy,color='kr'[ispin])
			if maxdos_output > 0:
				# If the user has specified a maximum DOS value, use it
				ax_dos.set_xlim(np.array([min(spinsgn[-1],0.0)-0.05,1.00])*maxdos_output)
			else:
				# Otherwise use the maximum DOS value read in
				ax_dos.set_xlim(np.array([min(spinsgn[-1],0.0)-0.05,1.05])*maxdos)
			if CUSTOM_YLIM:
				ax_dos.set_ylim(ylim_lower,ylim_upper)
			else:
				if PLOT_DOS or PLOT_DOS_TETRAHEDRON:
					ax_dos.set_ylim(energy[0],energy[-1])
				else:
					if PLOT_DOS_SPECIES or PLOT_DOS_SPECIES_TETRAHEDRON:
						ax_dos.set_ylim(species_energy[0],species_energy[-1])
		else:
			ax_dos.axvline(0,color='k',ls='--')
			ax_dos.axhline(0,color=(0.5,0.5,0.5))
			if PLOT_DOS_SPECIES or PLOT_DOS_SPECIES_TETRAHEDRON:
				for sp in range(len(species)):
					for ispin in range(max_spin_channel):
						ax_dos.plot(energy,tdos[sp][:,ispin]*spinsgn[ispin],color='br'[ispin],linestyle='-',label='%s %s'%(species[sp],['up','down'][ispin]))
						for l in range(ldos[sp].shape[2]):
							ax_dos.plot(energy,ldos[sp][:,ispin,l]*spinsgn[ispin],color='br'[ispin],linestyle='--',label='%s (l=%i) %s'%(species[sp],l,['up','down'][ispin]))
			if PLOT_DOS or PLOT_DOS_TETRAHEDRON:
				for ispin in range(max_spin_channel):
					ax_dos.plot(energy,dos[:,ispin]*spinsgn[ispin],color='br'[ispin])
			ax_dos.set_xlim(energy[0],energy[-1])
			if CUSTOM_YLIM:
				ax_dos.set_xlim(ylim_lower,ylim_upper)
			else:
				if maxdos_output > 0:
					# If the user has specified a maximum DOS value, use that instead
					ax_dos.set_ylim(np.array([min(spinsgn[-1],0.0)-0.05,1.00])*maxdos_output)
				else:
					# Otherwise use the maximum DOS value read in
					ax_dos.set_ylim(np.array([min(spinsgn[-1],0.0)-0.05,1.05])*maxdos)
			ax_dos.set_xlabel(r"$\varepsilon - \mu$ (eV)")
		
		if PLOT_DOS_SPECIES or PLOT_DOS_SPECIES_TETRAHEDRON:
			if SHOW_LEGEND:
				ax_dos.legend(bbox_to_anchor=(legend_x_offset, legend_y_offset))
#######################
	matplotlib.rcParams['savefig.dpi'] =  print_resolution
	matplotlib.rcParams['font.size'] = font_size
	matplotlib.rcParams['lines.linewidth'] = default_line_width
	#matplotlib.rcParams['lines.markersize'] = 1
	#plt.savefig(file_baseName+".png",transparent=True)
	#plt.savefig(file_baseName+".png")
	plt.savefig(file_baseName+".eps",format='eps',transparent=True)
#==================================================#
#def smoothdos(dos):
#	dos = np.asarray(dos)
#	return dos

Main()
#if __name__ == "__main__" :
# main(sys.argv[1], sys.argv[2], sys.argv[3], etc)
