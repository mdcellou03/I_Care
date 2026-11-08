import os 
import json
# recommendations.py
# Educational eye-health information for I_Care.
# This module does not prescribe medication or diagnose disease.

DISCLAIMER = (
    "I_Care is an experimental AI screening prototype. "
    "Its predictions are not medical diagnoses. "
    "Consult a qualified healthcare professional "
    "for medical advice."
)

URGENT_WARNING = (
    "Seek urgent medical attention for sudden vision loss, "
    "severe eye pain, significant light sensitivity, "
    "or a rapidly worsening eye condition, regardless "
    "of the AI result."
)

RECOMMENDATIONS = {
    "Cataract": {
        "title": "Possible Cataract",
        "description": (
            "A cataract is clouding of the natural lens "
            "inside the eye. It can cause blurry vision, "
            "glare, or difficulty seeing at night."
        ),
        "next_steps": [
            "Arrange an eye examination with an optometrist "
            "or ophthalmologist.",
            "Discuss any changes in vision or increased "
            "sensitivity to glare.",
            "Do not rely on a photograph alone to "
            "confirm a cataract."
        ],
        "urgency": "routine"
    },

    "Conjunctivitis": {
        "title": "Possible Conjunctivitis",
        "description": (
            "Conjunctivitis involves inflammation of "
            "the conjunctiva. Symptoms may include "
            "redness, irritation, watering, or discharge."
        ),
        "next_steps": [
            "Avoid rubbing your eyes and wash your hands "
            "regularly.",
            "Avoid sharing towels or eye cosmetics.",
            "Seek medical advice if symptoms persist, "
            "worsen, or involve pain or vision changes.",
            "If you wear contact lenses, remove them "
            "and seek prompt professional advice."
        ],
        "urgency": "monitor"
    },

    "Healthy": {
        "title": "No Abnormality Classified",
        "description": (
            "The model classified this image as Healthy. "
            "This does not confirm that the eye is healthy "
            "or rule out an eye condition."
        ),
        "next_steps": [
            "Continue routine eye examinations.",
            "Seek professional assessment if you have "
            "eye discomfort, redness, or vision changes.",
            "Do not ignore symptoms because of this result."
        ],
        "urgency": "routine"
    },

    "Jaundice": {
        "title": "Possible Yellowing of the Eyes",
        "description": (
            "Yellowing of the whites of the eyes can be "
            "associated with jaundice, which may indicate "
            "an underlying liver, blood, or bile duct condition."
        ),
        "next_steps": [
            "Seek prompt medical assessment if you notice "
            "new yellowing of the eyes.",
            "A healthcare professional may recommend "
            "blood tests or other investigations.",
            "Do not attempt to diagnose the cause "
            "using an image alone."
        ],
        "urgency": "prompt"
    },

    "Uveitis": {
        "title": "Possible Uveitis",
        "description": (
            "Uveitis is inflammation inside the eye. "
            "It may cause pain, redness, blurred vision, "
            "or sensitivity to light."
        ),
        "next_steps": [
            "Seek urgent assessment by an eye-care "
            "professional if uveitis is suspected.",
            "Do not delay assessment if you experience "
            "eye pain or changes in vision.",
            "Avoid using prescription eye medications "
            "without professional guidance."
        ],
        "urgency": "urgent"
    }
}


def get_recommendation(prediction):
    """
    Return educational information for a predicted class.

    Args:
        prediction (str): Model-predicted class name.

    Returns:
        dict: Information and recommended next steps.
    """

    info = RECOMMENDATIONS.get(prediction)

    if info is None:
        return {
            "title": "Unknown Classification",
            "description": (
                "The model could not match this prediction "
                "to a supported category."
            ),
            "next_steps": [
                "Consult a healthcare professional "
                "if you have eye-health concerns."
            ],
            "urgency": "unknown",
            "urgent_warning": URGENT_WARNING,
            "disclaimer": DISCLAIMER
        }

    return {
        **info,
        "urgent_warning": URGENT_WARNING,
        "disclaimer": DISCLAIMER
    }


# ==========================================
# COMMAND LINE TESTING
# ==========================================

if __name__ == "__main__":
    import json
    import sys

    prediction = (
        sys.argv[1] if len(sys.argv) > 1 else "Healthy"
    )

    result = get_recommendation(prediction)

    print(json.dumps(result, indent=2))