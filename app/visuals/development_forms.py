"""Inspection eligibility is independent of Main approval and player queues."""
from transition_catalog import SCENES

FRACTAL_FORMS={41:'Tidal Strata',42:'Recursive Atrium',43:'Honeycomb Garden'}
FRACTAL_STATES={41:'fractal_landscape',42:'fractal_atrium',43:'fractal_bloom'}
INSPECTION_FORMS={**SCENES,**FRACTAL_FORMS}


def inspection_eligible(form):
    return form in INSPECTION_FORMS
