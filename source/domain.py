import numpy as np
from source.arm import Arm, Placebo
from source.utils import stratified_randomization

class Domain:

    def __init__(self, arms, name, allocation=None):
        """
        Class describing a domain in the platform trial. Consists of multiple domains

        Parameters
        ----------
        arms: list-like of source.arm.Arm
            list of K interventions (not including placebo)
        name: str
            name of the domain
        allocation: None or vector of length K+1
            probability of randomizing to each domain
        """

        # Store some meta data
        self.name = name
        self.K = len(arms)  # Number of treatment arms
        self.ind = range(self.K+1)
        self.S = arms[0].S
        self.arms = [Placebo(strata=self.S)] + arms
        self.H = [self.K]

        # Default is equal randomization
        if allocation is None:
            self.allocation = np.ones(self.K+1)/(self.K+1)
        # Otherwise manual specification
        else:
            if len(allocation) == (self.K+1):
                self.allocation = allocation / allocation.sum()
            else:
                TypeError('length of allocation must be equal to the number of arms+1')

    def _get_arm_effects(self):
        """
        Returns the treatment effect in each arm

        Returns
        -------
        np.array of effects
        """

        return np.array([a.effects for a in self.arms])

    def _get_arm_names(self):
        """
        Returns the name of each arm

        Returns
        -------
        np.array of effects
        """

        return np.array([a.name for a in self.arms])

    def randomize_patients(self, strata):
        """
        Stratified randomization

        Parameters
        ----------
        strata

        Returns
        -------
        np.array of indices, indicating the arm to which a patient was randomized (0=placebo)
        """

        # Randomize
        inds = np.unique(strata)
        counts = [np.count_nonzero(strata == s) for s in inds]
        rands = [stratified_randomization(n, self.allocation) for n in counts]

        assignment = np.empty_like(strata)
        tots = [0 for i in inds]

        for n, s in enumerate(strata):
            assignment[n] = rands[s][tots[s]]
            tots[s] += 1

        return assignment

    def treatment_effect(self, strata, assignment):
        """
        Determines the treatment effect for this

        Parameters
        ----------
        strata
        assignment

        Returns
        -------

        """

        # Simulate the treatment effect
        arm_effects = self._get_arm_effects()
        effect = np.array([arm_effects[a, s] for a, s in zip(assignment, strata)])

        return effect

    def _get_prior(self):
        """ returns important aspects of the prior"""

        return {
            'n_components': 1,
            'n_means': [self.K],
            'n0s': [1.0],
            'As': np.array([])
        }


class CombinationDomain(Domain):

    def __init__(self, backbone, adjuvants, name):
        """ This arm explores combinations of backbone drugs with and without an adjuvant.
        Assumes the effects are additive.  Designed for the antihistamine domain, may not
        work as intended in other domains """

        # Add the combinations
        arms = [b for b in backbone]
        for a in adjuvants:
            for b in backbone:
                arms.append(Arm(name='{}+{}'.format(b.name, a.name), effects=b.effects+a.effects))

        # Create the allocation ratio
        allocation = np.repeat(1.0 / (1.0 + len(backbone)) / (1.0 + len(adjuvants)), 1 + len(arms))
        allocation[0] = 1.0 / (1 + len(backbone))

        Domain.__init__(self, arms=arms, name=name, allocation=allocation)

        # Some updates to the priors
        self.H = np.repeat(len(backbone), len(adjuvants)+1)
