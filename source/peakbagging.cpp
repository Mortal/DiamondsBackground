// Main code for peak bagging by means of nested sampling analysis
// Created by Enrico Corsaro @ IvS - 24 January 2013
// e-mail: enrico.corsaro@ster.kuleuven.be
// Source code file "peakbagging.cpp"

#include <cstdlib>
#include <iostream>
#include <iomanip>
#include <fstream>
#include "Functions.h"
#include "File.h"
#include "NestedSampler.h"

#include "UniformPrior.h"
#include "NormalLikelihood.h"
#include "LorentzianModel.h"
#include "Results.h"


int main(int argc, char *argv[])
{
    unsigned long Nrows;
    int Ncols;
    ArrayXXd data;
  

    // Check number of arguments for main function
    
    if (argc != 3)
    {
        cerr << "Usage: peakbagging <input file> <output directory>" << endl;
        exit(EXIT_FAILURE);
    }


    // Read data from input file specified

    ifstream inputFile(argv[1]);
    if (!inputFile.good())
    {
        cerr << "Error opening input file" << endl;
        exit(EXIT_FAILURE);
    }

    File::snifFile(inputFile, Nrows, Ncols);
    data = File::arrayXXdFromFile(inputFile, Nrows, Ncols);
    inputFile.close();

   
    // Creating arrays for each data type
    
    ArrayXd covariates = data.col(0);
    ArrayXd observations = data.col(1);
    ArrayXd uncertainties = data.col(2);
   

    // Choose fundamental parameters for the nested inference process

    int Nobjects = 100;      // Number of objects per nested iteration (usually 100)
    int Ndimensions = 3;        // Number of free parameters (dimensions) of the problem


    // Define boundaries of the free parameters of the problem (should be done with separate routine)

    ArrayXd parametersMinima(Ndimensions);
    ArrayXd parametersMaxima(Ndimensions);
    parametersMinima <<  0.0, 0.8, 1.0;         // Centroid, Amplitude, Gamma
    parametersMaxima << 20.0, 1.5, 3.0;
    
    
    // First step - Setting Prior distribution and parameter space

    UniformPrior prior(parametersMinima, parametersMaxima);


    // Second step - Setting up a model for the inference problem
    
    LorentzianModel model(covariates);
    

    // Third step - Setting up the likelihood function to be used
    
    NormalLikelihood likelihood(covariates, observations, uncertainties, model);
    

    // Fourth step - Starting nested sampling process
    
    NestedSampler nestedSampler(prior, likelihood);
    nestedSampler.run(Nobjects);


    // Save the results in an output file

    Results results(nestedSampler);
    string outputDirName(argv[2]);
    results.writeParametersToFile(outputDirName + "/parameter");
    results.writeLogLikelihoodToFile(outputDirName + "/likelihood.txt");
    results.writeEvidenceInformationToFile(outputDirName + "/evidence.txt");
    results.writePosteriorProbabilityToFile(outputDirName + "/posterior.txt");
    results.writeParameterEstimationToFile(outputDirName + "/parameterestimation.txt");
    
    return EXIT_SUCCESS;
}
