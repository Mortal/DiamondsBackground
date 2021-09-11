 # Python suite for execution and output handling of the Background code extension of DIAMONDS.
 #
 # Main Usage: 
 #   import background as bkg
 #   bkg.background_plot('KIC','012008916','00')        # To plot the background fit of the tutorial RGB star KIC012008916
 #   bkg.background_mpd('KIC','012008916','00')         # To plot the marginal probability distributions for the background parameters 
 #                                                        of the tutorial RGB star KIC012008916
 #   bkg.set_background_priors('KIC','012008916',162,'ThreeHarvey’,0)       # To generate priors and configuring parameters to run the background fit
 # ------------------------------------------------------------------------------------------------------

import numpy as np, matplotlib.pyplot as plt, glob, os
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib as mpl
pi=np.pi
prefix = 'background_'

def smooth(x, window_len=11, window='hanning'):
    """
    Author: Jean McKeever
    email: jean.mckeever@yale.edu
    Created: December 2020
    
    Smooth the data using a window with requested size.
    
    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal 
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.
    
    :param x: The input signal 
    :type x: array
    :param window_len: The dimension of the smoothing window; should be an odd
                       integer
    :type window_len: int
    :param window: The type of window from 'flat', 'hanning', 'hamming', 
                   'bartlett', 'blackman'. Flat window will produce a moving 
                   average smoothing.
    :type window: str
    :return The smoothed signal  
    :rtype array
    """

    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")
    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")
    if window_len<3:
        return x
    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError("Window is one of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")
    
    s=np.r_[x[window_len-1:0:-1],x,x[-2:-window_len-1:-1]]
    
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')

    y=np.convolve(w/w.sum(),s,mode='valid')
    
    return y[window_len//2:-window_len//2+1]

def get_working_paths(catalog_id,star_id,subdir):
    """
    Authors: Jean McKeever, Enrico Corsaro
    email: enrico.corsaro@inaf.it
    Created: 12 Aug 2016
    Edited: 1 June 2021
    INAF-OACT

    This method sets the working directories to locate the input data files and output files from the fit
    with DIAMONDS.

    :param catalog_id: the Catalog name of the star (e.g. KIC, TIC, etc.)
    :type catalog_id: str

    :param star_id: the ID number of the star
    :type star_id: str

    :param subdir: the output sub-directory where the ASCII files generated by DIAMONDS are stored
    :type subdir: str

    """

    local_path = str(np.loadtxt('../../build/localPath.txt',dtype='str'))
    data_dir = local_path + 'data/' 
    star_dir = local_path + 'results/' + catalog_id + star_id + '/'
    results_dir = star_dir + subdir + '/'
    return data_dir,star_dir,results_dir

def background_plot(catalog_id,star_id,subdir,params=None):
    """
    Authors: Jean McKeever, Enrico Corsaro
    email: enrico.corsaro@inaf.it
    Created: 12 Aug 2016
    Edited: 1 June 2021
    INAF-OACT

    This method plots the global background fit on top of the stellar power spectral density
    as well as the individual components of the background model. The output plot is stored in a EPS file
    inside the star folder.

    :param catalog_id: the Catalog name of the star (e.g. KIC, TIC, etc.)
    :type catalog_id: str

    :param star_id: the ID number of the star
    :type star_id: str

    :param subdir: the output sub-directory where the ASCII files generated by DIAMONDS are stored
    :type subdir: str

    :param params: optional input parameter containing the values of the model free parameters
    :type params: array of floats

    """

    mpl.rcParams['xtick.labelsize']='medium'
    mpl.rcParams['ytick.labelsize']='medium'
   
    data_dir,star_dir,results_dir = get_working_paths(catalog_id,star_id,subdir)
    freq,psd = get_background_data(catalog_id,star_id,data_dir) 
    model_name = get_background_name(catalog_id,star_id,results_dir)

    if params == None:
        params = get_background_params(catalog_id,star_id,results_dir)
    else:
        params = params

    # -------------------------------------------------------------------------------------------------------
    # Define some general parameters useful within the computations
    # -------------------------------------------------------------------------------------------------------
    numax = params[-2]
    dnu = 0.267*numax**0.760
    freqbin = freq[1]-freq[0]
    width = dnu/2./freqbin
    win_len=int(width)
    if win_len % 2 == 0: win_len += 1
    psd_smth = smooth(psd,window_len=win_len,window='flat')

    # -------------------------------------------------------------------------------------------------------
    # Plot the region of PSD containing the fitted background components
    # -------------------------------------------------------------------------------------------------------
    pdf = PdfPages(star_dir + catalog_id + star_id + '_' + subdir + '_Background.pdf')
    fig = plt.figure(1,figsize=(10,4))
    plt.clf()
    ax1 = plt.subplot(1,1,1)
    plt.loglog(freq,psd,color='grey')
    plt.xlim(0.1, np.max(freq))
    plt.ylim(1,np.max(psd))
    plt.xlabel(r'Frequency [$\mu$Hz]')
    plt.ylabel(r'PSD [ppm$^2$/$\mu$Hz]')
    ax1.tick_params(width=1.5,length=8,top=True,right=True)
    ax1.tick_params(which='minor',length=6,top=True,right=True)
    plt.plot(freq,psd_smth,'k',lw=2)
    b1,b2,h_long,h_gran1,h_gran2,g,w,h_color=background_function(params,freq,model_name)
    plt.plot(freq,g,'m-.',lw=2)
    plt.plot(freq,h_color,'y-.',lw=2)
    plt.plot(freq,h_long,'b-.',lw=2)
    plt.plot(freq,h_gran1,'b-.',lw=2)
    plt.plot(freq,h_gran2,'b-.',lw=2)
    plt.plot(freq,w,'y-.',lw=2)
    plt.plot(freq,b1,'r-',lw=3)
    plt.plot(freq,b2,'g--',lw=2)
    plt.subplots_adjust(left=.12,right=.97,top=.94,bottom=.2)
    
    plt.text(.1,.075,'%s%s'% (catalog_id,star_id), size='large', transform=ax1.transAxes)
    pdf.savefig()
    pdf.close()
    return

def background_mpd(catalog_id,star_id,subdir):
    """
    Authors: Jean McKeever, Enrico Corsaro
    email: enrico.corsaro@inaf.it
    Created: 12 Aug 2016
    Edited: 1 June 2021
    INAF-OACT

    This method plots the marginal distributions for each of the fitted background parameters
    as well as the region of the credible intervals. The output plot is stored in a EPS file
    inside the star folder.

    :param catalog_id: the Catalog name of the star (e.g. KIC, TIC, etc.)
    :type catalog_id: str

    :param star_id: the ID number of the star
    :type star_id: str

    :param subdir: the output sub-directory where the ASCII files generated by DIAMONDS are stored
    :type subdir: str

    """
    
    mpl.rcParams['xtick.labelsize']='x-small'
    mpl.rcParams['ytick.labelsize']='x-small'
    
    data_dir,star_dir,results_dir = get_working_paths(catalog_id,star_id,subdir)
    model_name = get_background_name(catalog_id,star_id,results_dir)

    plot_labels = [r'W [ppm$^2$/$\mu$Hz]',
                   r'$\sigma_{color}$ [ppm]',
                   r'$\nu_{color}$ [$\mu$Hz]',
                   r'$\sigma_{long}$ [ppm]',
                   r'$\nu_{long}$ [$\mu$Hz]',
                   r'$\sigma_{gran,1}$ [ppm]',
                   r'$\nu_{gran,1}$ [$\mu$Hz]',
                   r'$\sigma_{gran,2}$ [ppm]',
                   r'$\nu_{gran,2}$ [$\mu$Hz]',
                   r'H$_{osc}$ [ppm$^2$/$\mu$Hz]',
                   r'$\nu_{max} [$\mu$Hz]$',
                   r'$\sigma_{env}$ [$\mu$Hz]']
   
    meanpar,medianpar,modepar,lowerpar,upperpar = np.loadtxt(results_dir + prefix + 'parameterSummary.txt',unpack=True,usecols=(0,1,2,4,5))
    n_param = medianpar.size

    if model_name == 'FlatNoGaussian':
        plot_labels = [plot_labels[0]]

    if model_name == 'Flat':
        plot_labels = [plot_labels[0]] + plot_labels[-3:]

    if model_name == 'OneHarveyNoGaussian':
        plot_labels = [plot_labels[0]] + plot_labels[5:7]

    if model_name == 'OneHarvey':
        plot_labels = [plot_labels[0]] + plot_labels[5:7] + plot_labels[-3:]

    if model_name == 'OneHarveyColor':
        plot_labels = plot_labels[0:3] + plot_labels[5:7] + plot_labels[-3:]

    if model_name == 'TwoHarveyNoGaussian':
        plot_labels = [plot_labels[0]] + plot_labels[5:9]
    
    if model_name == 'TwoHarvey':
        plot_labels = [plot_labels[0]] + plot_labels[5:]
    
    if model_name == 'TwoHarveyColor':
        plot_labels = plot_labels[0:3] + plot_labels[5:7] + plot_labels[-3:]
    
    if model_name == 'ThreeHarveyNoGaussian':
        plot_labels = [plot_labels[0]] + plot_labels[5:9]
    
    if model_name == 'ThreeHarvey':
        plot_labels = [plot_labels[0]] + plot_labels[3:]
    
    pdf = PdfPages(star_dir + catalog_id + star_id + '_' + subdir + '_MarginalDistributions.pdf')
    plt.ion()
    fig = plt.figure(2,figsize=(11,7))
    plt.clf()

    for parnumb in range(0,n_param-1):
        if parnumb < 10:
            parstr = '0' + str(parnumb)
        else:
            parstr = str(parnumb)
        
        par,marg = np.loadtxt(results_dir + prefix + 'marginalDistribution0' + parstr + '.txt',unpack=True)
        plt.subplot(4,3,parnumb+1)
        plt.plot(par,marg,'k-')
        plt.xlim(np.min(par),np.max(par))
        plt.ylim(0,np.max(marg)*1.1)
        plt.title(plot_labels[parnumb],fontsize='small')
        plt.ylabel('MPD',fontsize='small')
        tmpci = np.where((par>lowerpar[parnumb])&(par<upperpar[parnumb]))[0]
        ci = par[tmpci]
        postci = marg[tmpci]
        plt.fill_between(ci,postci,color='blue',alpha=.4)
        plt.vlines(modepar[parnumb],0,max(marg),lw=1,color='k',linestyle='--')

    plt.subplots_adjust(hspace=.5,wspace=.35,left=.08,bottom=.05,top=.93,right=.98)
    pdf.savefig()
    pdf.close()
    return

def background_parhist(catalog_id,star_id,subdir):
    """
    Authors: Jean McKeever, Enrico Corsaro
    email: enrico.corsaro@inaf.it
    Created: 12 Aug 2016
    Edited: 1 June 2021
    INAF-OACT

    This method computes a quick histogram for when DIAMONDS fails to compute the MPDs. It can be useful for fixing priors.

    :param catalog_id: the Catalog name of the star (e.g. KIC, TIC, etc.)
    :type catalog_id: str

    :param star_id: the ID number of the star
    :type star_id: str

    :param subdir: the output sub-directory where the ASCII files generated by DIAMONDS are stored
    :type subdir: str

    """

    mpl.rcParams['xtick.labelsize']='x-small'
    mpl.rcParams['ytick.labelsize']='x-small'

    data_dir,star_dir,results_dir = get_working_paths(catalog_id,star_id,subdir)
    model_name = get_background_name(catalog_id,star_id,results_dir)

    filename_summary = np.sort(glob.glob(results_dir + prefix + 'parameter0*.txt'))
    nparam = filename_summary.size

    plot_labels = [r'W [ppm$^2$/$\mu$Hz]',
                   r'$\sigma_{color}$ [ppm]',
                   r'$\nu_{color}$ [$\mu$Hz]',
                   r'$\sigma_{long}$ [ppm]',
                   r'$\nu_{long}$ [$\mu$Hz]',
                   r'$\sigma_{gran,1}$ [ppm]',
                   r'$\nu_{gran,1}$ [$\mu$Hz]',
                   r'$\sigma_{gran,2}$ [ppm]',
                   r'$\nu_{gran,2}$ [$\mu$Hz]',
                   r'H$_{osc}$ [ppm$^2$/$\mu$Hz]',
                   r'$\nu_{max} [$\mu$Hz]$',
                   r'$\sigma_{env}$ [$\mu$Hz]']

    plt.ion()
    fig = plt.figure(3,figsize=(11,7))
    plt.clf()

    for parnumb in range(0,nparam-1):
        if parnumb < 10:
            parstr = '0' + str(parnumb)
        else:
            parstr = str(parnumb)

        name = prefix + 'parameter0'
        par = np.loadtxt(result_dir + name + parstr + '.txt')
        plt.subplot(4,3,parnumb+1)
        plt.hist(par)
        plt.title(plot_labels[parnumb],fontsize='small')
    plt.subplots_adjust(hspace=.5,wspace=.35,left=.08,bottom=.05,top=.93,right=.98)
    plt.text(.5,.07,'%s%s'% (catalog_id,star_id) ,size='large', transform=ax.transAxes)
    return

def background_function(params,freq,model_name):
    """
    Authors: Enrico Corsaro
    email: enrico.corsaro@inaf.it
    Created: 12 Aug 2016
    Edited: 1 June 2021
    INAF-OACT

    This method generates the background model from a list of possible choices as implemented in
    the Background code extension of DIAMONDS.

    :param params: the input values of the free parameters to generate the model prediction
    :type params: array of floats

    :param freq: the input frequency array for which the background prediction has to be computed
    :type freq: array of floats

    :param model_name: the name of the background model to generate the predictions
    :type model_name: str

    """

    if model_name == 'FlatNoGaussian':
        w = params
        amp_long,freq_long,amp_gran1,freq_gran1,amp_gran2,freq_gran2,amp_color,freq_color,hg,numax,sigma = 0,1,0,1,0,1,0,1,0,1,1

    if model_name == 'Flat':
        w,hg,numax,sigma = params
        amp_long,freq_long,amp_gran1,freq_gran1,amp_gran2,freq_gran2,amp_color,freq_color = 0,1,0,1,0,1,0,1

    if model_name == 'OneHarveyNoGaussian':
        w,amp_gran1,freq_gran1 = params
        amp_long,freq_long,amp_gran2,freq_gran2,amp_color,freq_color,hg,numax,sigma = 0,1,0,1,0,1,0,1,1

    if model_name == 'OneHarvey':
        w,amp_gran1,freq_gran1,hg,numax,sigma = params
        amp_long,freq_long,amp_gran2,freq_gran2,amp_color,freq_color = 0,1,0,1,0,1

    if model_name == 'OneHarveyColor':
        w,amp_color,freq_color,amp_gran1,freq_gran1,hg,numax,sigma = params
        amp_long,freq_long,amp_gran2,freq_gran2 = 0,1,0,1

    if model_name == 'TwoHarveyNoGaussian':
        w,amp_gran1,freq_gran1,amp_gran2,freq_gran2 = params
        amp_long,freq_long,amp_color,freq_color,hg,numax,sigma = 0,1,0,1,0,1,1

    if model_name == 'TwoHarvey':
        w,amp_gran1,freq_gran1,amp_gran2,freq_gran2,hg,numax,sigma = params
        amp_long,freq_long,amp_color,freq_color = 0,1,0,1

    if model_name == 'TwoHarveyColor':
        w,amp_color,freq_color,amp_gran1,freq_gran1,amp_gran2,freq_gran2,hg,numax,sigma = params
        amp_long,freq_long = 0,1

    if model_name == 'ThreeHarveyNoGaussian':
        w,amp_long,freq_long,amp_gran1,freq_gran1,amp_gran2,freq_gran2 = params
        amp_color,freq_color,hg,numax,sigma = 0,1,0,1,1

    if model_name == 'ThreeHarvey':
        w,amp_long,freq_long,amp_gran1,freq_gran1,amp_gran2,freq_gran2,hg,numax,sigma = params
        amp_color,freq_color = 0,1
   
    if model_name == 'ThreeHarveyColor':
        w,amp_color,freq_color,amp_long,freq_long,amp_gran1,freq_gran1,amp_gran2,freq_gran2,hg,numax,sigma = params    

    zeta = 2.0*np.sqrt(2.0)/pi
    nyq = 283.2116656017908
    
    r = (np.sin(pi/2. * freq/nyq) / (pi/2. * freq/nyq))**2
    
    h_long = zeta * r * (amp_long**2/freq_long) / (1 + (freq/freq_long)**4)
    h_gran1 = zeta * r *(amp_gran1**2/freq_gran1) / (1 + (freq/freq_gran1)**4)
    h_gran2 = zeta * r *(amp_gran2**2/freq_gran2) / (1 + (freq/freq_gran2)**4)
    h_color = 2*pi*amp_color*amp_color/(freq_color*(1+(freq/freq_color)**2)) 
    
    g = r * hg * np.exp(-(numax-freq)**2/(2.*sigma**2))
    
    b1 = h_long + h_gran1 + h_gran2 + w + h_color
    b2 = h_long + h_gran1 + h_gran2 + g + w + h_color
   
    w = np.zeros(freq.size) + w 

    return b1,b2,h_long,h_gran1,h_gran2,g,w,h_color

def get_background_params(catalog_id,star_id,results_dir):
    """
    Authors: Jean McKeever, Enrico Corsaro
    email: enrico.corsaro@inaf.it
    Created: 12 Aug 2016
    Edited: 1 June 2021
    INAF-OACT

    This method reads the Background parameter summary file from DIAMONDS. This file contains the final 
    estimates for each free parameter of the model.

    :param catalog_id: the Catalog name of the star (e.g. KIC, TIC, etc.)
    :type catalog_id: str

    :param star_id: the ID number of the star
    :type star_id: str

    :param results_dir: the output directory where the ASCII files generated by DIAMONDS are stored
    :type results_dir: str

    """

    params = np.loadtxt(results_dir + prefix + 'parameterSummary.txt',usecols=(1,))
    return params

def get_background_data(catalog_id,star_id,data_dir):
    """
    Authors: Jean McKeever, Enrico Corsaro
    email: enrico.corsaro@inaf.it
    Created: 12 Aug 2016
    Edited: 1 June 2021
    INAF-OACT

    This method reads the PSD of the star

    :param catalog_id: the Catalog name of the star (e.g. KIC, TIC, etc.)
    :type catalog_id: str

    :param star_id: the ID number of the star
    :type star_id: str

    :param data_dir: the directory where the data file of the star is stored
    :type data_dir: str

    """

    freq,psd = np.loadtxt(data_dir + catalog_id + star_id +'.txt',unpack=True)
    return freq,psd

def get_background_name(catalog_id,star_id,results_dir):
    """
    Authors: Jean McKeever, Enrico Corsaro
    email: enrico.corsaro@inaf.it
    Created: 12 Aug 2016
    Edited: 1 June 2021
    INAF-OACT

    This method obtains the model name of the background used for the fit with Background+DIAMONDS codes

    :param catalog_id: the Catalog name of the star (e.g. KIC, TIC, etc.)
    :type catalog_id: str

    :param star_id: the ID number of the star
    :type star_id: str

    :param results_dir: the output directory where the ASCII files generated by DIAMONDS are stored
    :type results_dir: str

    """

    config = np.loadtxt(results_dir + prefix + 'computationParameters.txt',unpack=True,dtype=str)
    bg_name = config[-2]

    print(' ----------------------------------------------------------------- ')
    print(' The background model adopted for ' + catalog_id + star_id + ' is ' + bg_name)
    print(' ----------------------------------------------------------------- ')
    return bg_name

def single_parameter_evolution(catalog_id,star_id,subdir,parameter):
    """
    Authors: Kevin Fusshoeller, Enrico Corsaro
    email: enrico.corsaro@inaf.it
    Created: April 2016
    Edited: 3 June 2021
    INAF-OACT

    This method plots the evolution of an input free parameter of the background model by means of
    the nested sampling computed by DIAMONDS.

    :param catalog_id: the Catalog name of the star (e.g. KIC, TIC, etc.)
    :type catalog_id: str

    :param star_id: the ID number of the star
    :type star_id: str

    :param subdir: the output sub-directory where the ASCII files generated by DIAMONDS are stored
    :type subdir: str

    :param parameter: the number of the free parameter for which the parameter evolution is desired
    :type parameter: int
    """

    data_dir,star_dir,results_dir = get_working_paths(catalog_id,star_id,subdir)
    if parameter < 10:
        parstr = '0' + str(parameter)
    else:
        parstr = str(parameter)
    sampling = np.loadtxt(results_dir + prefix + 'parameter0' + parstr + '.txt',unpack=True)

    plt.ion()
    fig = plt.figure(4,figsize=(11,4))
    plt.clf()
    ax1 = plt.subplot(1,1,1)
    plt.xlim(0,sampling.size)
    plt.ylim(np.min(sampling),np.max(sampling))
    plt.xlabel(r'Nested iteration')
    plt.ylabel(r'Parameter 0' + parstr)
    ax1.tick_params(width=1.5,length=8,top=True,right=True)
    ax1.tick_params(which='minor',length=6,top=True,right=True)
    plt.plot(np.arange(sampling.size),sampling,'k',lw=2)


def parameter_evolution(catalog_id,star_id,subdir):
    """
    Authors: Kevin Fusshoeller, Enrico Corsaro
    email: enrico.corsaro@inaf.it
    Created: April 2016
    Edited: 3 June 2021
    INAF-OACT

    This method plots the evolution of all the free parameters used in the background model by means
    of the nested sampling computed by DIAMONDS.

    :param catalog_id: the Catalog name of the star (e.g. KIC, TIC, etc.)
    :type catalog_id: str

    :param star_id: the ID number of the star
    :type star_id: str

    :param subdir: the output sub-directory where the ASCII files generated by DIAMONDS are stored
    :type subdir: str
    """

    data_dir,star_dir,results_dir = get_working_paths(catalog_id,star_id,subdir)
    filename_summary = np.sort(glob.glob(results_dir + prefix + 'parameter0*.txt'))
    nparam = filename_summary.size
    
    plt.ion()
    fig = plt.figure(5,figsize=(11,7))
    plt.clf()

    for parnumb in range(0,nparam-1):
        if parnumb < 10:
            parstr = '0' + str(parnumb)
        else:
            parstr = str(parnumb)

        sampling = np.loadtxt(results_dir + prefix + 'parameter0' + parstr + '.txt',unpack=True)
        plt.subplot(4,3,parnumb+1)
        plt.xlim(0,sampling.size)
        plt.ylim(np.min(sampling),np.max(sampling))
        plt.xlabel(r'Nested iteration')
        plt.ylabel(r'Parameter 0' + parstr)
        plt.subplots_adjust(left=.12,right=.97,top=.94,bottom=.2)
        plt.plot(np.arange(sampling.size),sampling,'k',lw=2)
    
    plt.subplots_adjust(hspace=.5,wspace=.35,left=.08,bottom=.05,top=.93,right=.98)


def set_background_priors(catalog_id,star_id,numax,model_name,dir_flag=0):
    """
    Author: Enrico Corsaro
    email: enrico.corsaro@inaf.it
    Created: January 2021
    INAF-OACT

    This method creates all the files needed for the background fitting of a star using DIAMONDS.

    :param catalog_id: the Catalog name of the star (e.g. KIC, TIC, etc.)
    :type catalog_id: str

    :param star_id: the ID number of the star
    :type star_id: str

    :param numax: a raw guess for the value of nuMax
    :type numax: float

    :param model_name: the background model for which priors are desired
    :type model_name: str

    :param dir_fglag: the number for the subfolder to contain the fitting results
    :type dir_flag: int

    """ 

    print(' ---------------------------------------------- ')
    print(' Creating Background priors for ' + catalog_id + star_id)
    print(' ---------------------------------------------- ')
    
    data_dir,star_dir,results_dir = get_working_paths(catalog_id,star_id,'0')
    freq,psd = get_background_data(catalog_id,star_id,data_dir)

    numax_range = numax*0.1
    lower_numax = numax - numax_range
    upper_numax = numax + numax_range
    dnu = 0.267*numax**0.760
    sigma = 2.0 * dnu
    sigma_range = sigma*0.4
    lower_sigma = sigma - sigma_range*1.5
    upper_sigma = sigma + sigma_range

    freqbin = freq[1] - freq[0]
    smth_bins = int(dnu/freqbin)
    psd_smth = smooth(psd, window_len=smth_bins, window='flat')

    interesting_zone = np.where((freq > numax - 3*dnu) & (freq < numax + 3*dnu))[0]
    height = np.max(psd_smth[interesting_zone])
    lower_height = 0.1 * height
    upper_height = 1.40 * height


    # Define the priors for the white noise
    
    if np.max(freq) < 300 & numax > 200:
        tmp_w = np.where(freq > 200.)[0]
    else: 
        tmp_w = np.where(freq > numax+2*dnu)[0]
    
    if len(tmp_w) != 0:
        white_noise_array = psd[tmp_w]
    else:
        tmp_w = np.where(freq > numax)[0]
        white_noise_array = psd[tmp_w]
    
    white_noise = np.mean(white_noise_array)
    lower_white_noise = 0.5 * white_noise 
    upper_white_noise = 1.50 * white_noise 


    # Define the priors for the meso-granulation

    nu_g1 = 0.317 * numax**0.970
    lower_nu_g1 = 0.6 * nu_g1 
    upper_nu_g1 = 1.4 * nu_g1
    amp_g1 = 3383 * numax**-0.609
    
    g1_range = nu_g1 * 0.1
    tmp_g1 = np.where((freq >= nu_g1 - g1_range) & (freq <= nu_g1 + g1_range))[0]
    psd_g1 = np.max(psd[tmp_g1])
    amp_g1_data = np.sqrt(psd_g1*nu_g1)/(2*np.sqrt(2))*np.pi
    
    if amp_g1_data > amp_g1:
        amp_g1 = amp_g1_data
    
    lower_amp_g1 = 0.3 * amp_g1
    upper_amp_g1 = 1.5 * amp_g1 


    # Define the priors for the granulation 

    nu_g2 = 0.948 * numax**0.992
    lower_nu_g2 = 0.6 * nu_g2 
    upper_nu_g2 = 1.4 * nu_g2

    amp_g2 = 3383 * numax**-0.609
    lower_amp_g2 = 0.2 * amp_g1
    upper_amp_g2 = 1.5 * amp_g1 


    # Define the priors for the rotation
    # Make sure this is not overlapping with the meso-granulation

    nu_rot = nu_g1/2. 
    lower_nu_rot = np.min(freq)
    upper_nu_rot = 0.9 * nu_g1
    
    rot_range = nu_rot * 0.1
    tmp_rot = np.where((freq >= nu_rot - rot_range) & (freq <= nu_rot + rot_range))[0]
    psd_rot = np.max(psd[tmp_rot])
    amp_rot = np.sqrt(psd_rot*nu_rot)/(2*np.sqrt(2))*np.pi
    lower_amp_rot = 0.0
    upper_amp_rot = 1.5 * amp_rot


    # Define the priors for the colored noise

    nu_color = nu_rot*1.5
    lower_nu_color = np.min(freq)
    upper_nu_color = nu_color*1.5 
    amp_color = 0.0
    lower_amp_color = 0.0
    upper_amp_color = 2.0 * amp_rot


    # Checks for no overlap between prior ranges

    if upper_nu_g1 > lower_nu_g2 * 1.2:
        difference = upper_nu_g1 - lower_nu_g2
        upper_nu_g1 -= 0.5 * difference
        lower_nu_g2 += 0.5 * difference
    elif upper_nu_g1 < lower_nu_g2:
        # Make prior ranges to be contiguous
        upper_nu_g1 = (upper_nu_g1 + lower_nu_g2) / 2.0
        lower_nu_g2 = upper_nu_g1

    if upper_nu_rot > lower_nu_g1 * 1.3:
        difference = upper_nu_rot - lower_nu_g1
        upper_nu_rot -= 0.5 * difference
        lower_nu_g1 += 0.5 * difference
    elif upper_nu_rot < lower_nu_g1:
        # Make prior ranges to be contiguous
        upper_nu_rot = (upper_nu_rot + lower_nu_g1) / 2.0 
        lower_nu_g1 = upper_nu_rot

    
    # Set prior boundaries for the given background model

    if model_name == 'FlatNoGaussian':
        boundaries = [lower_white_noise,upper_white_noise]
    
    if model_name == 'OneHarveyNoGaussian':
        lower_nu_g1 = np.min(freq)
        boundaries = [lower_white_noise, upper_white_noise, lower_amp_g1, upper_amp_g1, lower_nu_g1, upper_nu_g1]
    
    if model_name == 'TwoHarveyNoGaussian':
        lower_nu_g1 = np.min(freq)
        boundaries = [lower_white_noise, upper_white_noise, lower_amp_g1, upper_amp_g1, lower_nu_g1, upper_nu_g1, lower_amp_g2, upper_amp_g2, 
                        lower_nu_g2, upper_nu_g2]
    
    if model_name == 'ThreeHarveyNoGaussian':
        boundaries = [lower_white_noise, upper_white_noise, lower_amp_rot, upper_amp_rot, lower_nu_rot, upper_nu_rot, lower_amp_g1, upper_amp_g1, 
                        lower_nu_g1, upper_nu_g1, lower_amp_g2, upper_amp_g2, lower_nu_g2, upper_nu_g2]
    
    if model_name == 'Flat':
        boundaries = [lower_white_noise, upper_white_noise, lower_height, upper_height, lower_numax, upper_numax, lower_sigma, upper_sigma]
    
    if model_name == 'OneHarvey':
        lower_nu_g1 = np.min(freq)
        boundaries = [lower_white_noise, upper_white_noise, lower_amp_g1, upper_amp_g1, lower_nu_g1, upper_nu_g1, 
                        lower_height, upper_height, lower_numax, upper_numax, lower_sigma, upper_sigma]
    
    if model_name == 'OneHarveyColor':
        lower_nu_g1 = np.min(freq)
        boundaries = [lower_white_noise, upper_white_noise, lower_amp_color, upper_amp_color, lower_nu_color, upper_nu_color, 
                        lower_amp_g1, upper_amp_g1, lower_nu_g1, upper_nu_g1, 
                        lower_height, upper_height, lower_numax, upper_numax, lower_sigma, upper_sigma]
    
    if model_name == 'TwoHarvey':
        lower_nu_g1 = np.min(freq)
        boundaries = np.array([lower_white_noise, upper_white_noise, lower_amp_g1, upper_amp_g1, lower_nu_g1, upper_nu_g1, lower_amp_g2, upper_amp_g2, 
                        lower_nu_g2, upper_nu_g2, lower_height, upper_height, lower_numax, upper_numax, lower_sigma, upper_sigma])
    
    if model_name == 'TwoHarveyColor':
        lower_nu_g1 = np.min(freq)
        boundaries = [lower_white_noise, upper_white_noise, lower_amp_color, upper_amp_color, lower_nu_color, upper_nu_color, 
                        lower_amp_g1, upper_amp_g1, lower_nu_g1, upper_nu_g1, lower_amp_g2, upper_amp_g2, 
                        lower_nu_g2, upper_nu_g2, lower_height, upper_height, lower_numax, upper_numax, lower_sigma, upper_sigma]

    if model_name == 'ThreeHarvey':
        boundaries = [lower_white_noise, upper_white_noise, lower_amp_rot, upper_amp_rot, lower_nu_rot, upper_nu_rot, 
                        lower_amp_g1, upper_amp_g1, lower_nu_g1, upper_nu_g1, lower_amp_g2, upper_amp_g2, 
                        lower_nu_g2, upper_nu_g2, lower_height, upper_height, lower_numax, upper_numax, lower_sigma, upper_sigma]
    
    if model_name == 'ThreeHarveyColor':
        boundaries = [lower_white_noise, upper_white_noise, lower_amp_color, upper_amp_color, lower_nu_color, upper_nu_color, 
                        lower_amp_rot, upper_amp_rot, lower_nu_rot, upper_nu_rot, lower_amp_g1, upper_amp_g1, lower_nu_g1, upper_nu_g1, 
                        lower_amp_g2, upper_amp_g2, lower_nu_g2, upper_nu_g2, lower_height, upper_height, lower_numax, upper_numax, lower_sigma, upper_sigma]


    # Write an ASCII file for the priors
    
    if dir_flag < 10:
        subdir_str = '0' + str(dir_flag)
    else:
        subdir_str = str(dir_flag)

    if not os.path.isdir(star_dir + subdir_str):
        os.mkdir(star_dir + subdir_str)

    filename = star_dir + 'background_hyperParameters_' + subdir_str + '.txt'

    header="""
    Hyper parameters used for setting up uniform priors.
    Each line corresponds to a different free parameter (coordinate).
    Column #1: Minima (lower boundaries)
    Column #2: Maxima (upper boundaries)
    """

    boundaries = np.reshape(np.array(boundaries),(int(len(boundaries)/2),2))
    np.savetxt(filename, boundaries,fmt='%.3f',header=header)


    # Write an ASCII file for the nested sampler configuring parameters.

    filename = star_dir + 'NSMC_configuringParameters.txt'
    NSMC_array = np.array([500, 500, 50000, 1000, 50, 1.5363, 0.0, 1.0])
    np.savetxt(filename, NSMC_array.T,fmt='%.1f')


    # Write a file with the value of the Nyquist

    filename = star_dir + 'NyquistFrequency.txt'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as f:
        f.write('{}'.format(np.max(freq)))

    #np.savetxt(filename, np.array(np.max(freq)),fmt='%.6f')


    # Write a file with the parameters for the X means clustering algorithm.

    filename = star_dir + 'Xmeans_configuringParameters.txt'
    xmeans_array = np.array([3, 6])
    np.savetxt(filename, xmeans_array.T,fmt='%d')