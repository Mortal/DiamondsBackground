#include "NestedSampler.h"

// NestedSampler::NestedSampler()
//
// PURPOSE: 
//      Class constructor
//
// INPUT:
//      variate: a RandomVariate class used as Prior to draw from
//
// OUTPUT:

NestedSampler::NestedSampler(RandomVariate &variate)
: randomVariate(variate), informationH(0.0), logEvidence(-DBL_MAX)
{

}






// NestedSampler::getLogEvidence()
//
// PURPOSE:
//
// INPUT:
//
// OUTPUT:

double NestedSampler::getLogEvidence()
{
    return logEvidence;
}








// NestedSampler::getLogEvidenceError()
//
// PURPOSE:
//
// INPUT:
//
// OUTPUT:

double NestedSampler::getLogEvidenceError()
{
    return logEvidenceError;
}







// NestedSampler::getInformationH()
//
// PURPOSE:
//
// INPUT:
//
// OUTPUT:

double NestedSampler::getInformationH()
{
    return informationH;
}








// NestedSampler::run()
//
// PURPOSE:
//      Start nested sampling computation. Save results in 
//      public vectors "logLikelihoodOfPosteriorSample", "posteriorSample", "results"
//
// INPUT:
//      Nobjects = Number of objects for nested sampling
//      Niter = Number of nested iterations
//
// OUTPUT:

void NestedSampler::run(int Nobjects, int Niter)
{
    double logWidthInPriorMass;
    double logLikelihoodConstraint;
    double logEvidenceNew;
    int copy;
    int worst;

    // Set vector sizes
    
    param.resize(Nobjects);
    logLikelihood.resize(Nobjects);
    logWeight.resize(Niter);
    posteriorSample.resize(Niter);
    logLikelihoodOfPosteriorSample.resize(Niter);
    posteriorSample.resize(Niter);

    // Initialize prior values
    
    randomVariate.drawNestedValues(param, logLikelihood, Nobjects);
    
    // Initialize prior mass interval
    
    logWidthInPriorMass = log(1.0 - exp(-1.0/Nobjects));  

    // Nested sampling loop
    
    for (int nest = 0; nest < Niter; nest++)
    {
        // Find worst object in the collection
        
        worst = 0;
        for (int i = 1; i < Nobjects; i++)
        {
            if (logLikelihood.at(i) < logLikelihood.at(worst))
            {
                worst = i;
            }
        }
        logWeight.at(worst) = logWidthInPriorMass + logLikelihood.at(worst);                
        
        // Update evidence Z and information H
        
        logEvidenceNew = MathExtra::logExpSum(logEvidence, logWeight.at(worst));
        informationH = updateInformationGain(informationH, logEvidence, logEvidenceNew, worst);
        logEvidence = logEvidenceNew;

        // Save nested samples for posterior

        posteriorSample.at(nest) = param.at(worst);                         // save parameter value
        logLikelihoodOfPosteriorSample.at(nest) = logLikelihood.at(worst);  // save corresponding likelihood
    
        // Replace worst object in favour of a copy of different survivor
        
        srand(time(0));
        do 
        {
            copy = rand() % Nobjects;              // 0 <= copy < Nobjects
        } 
        while (copy == worst && Nobjects > 1);     // do not replace if Nobjects = 1

        logLikelihoodConstraint = logLikelihood.at(worst);
        param.at(worst) = param.at(copy);
        logLikelihood.at(worst) = logLikelihood.at(copy);
        
        // Evolve the replaced object with the new constraint logLikelihood > logLikelihoodConstraint
        
        randomVariate.drawNestedValueWithConstraint(param.at(worst), logLikelihood.at(worst), logLikelihoodConstraint);
        
        // Shrink interval
        
        logWidthInPriorMass -= 1.0 / Nobjects;

        // Save the results to public data member
    }
    
    // Compute uncertainty on the log of the Evidence Z
    
    logEvidenceError = sqrt(fabs(informationH)/Nobjects);

    return;
}













// NestedSampler::updateInformationGain() 
//
// PURPOSE: 
//      Updates the information gain from old to new evidence
//
// INPUT:
//      H_old = Old information H
//      logEvidence_old = old log Evidence
//      logEvidence_new = new log Evidence
//
// OUTPUT:
//      New value of information gain H

double NestedSampler::updateInformationGain(double H_old, double logEvidence_old, double logEvidence_new, int worst)
{    
    return exp(logWeight[worst] - logEvidence_new) * logLikelihood[worst]
           + exp(logEvidence_old - logEvidence_new) * (H_old + logEvidence_old) - logEvidence_new;
}

