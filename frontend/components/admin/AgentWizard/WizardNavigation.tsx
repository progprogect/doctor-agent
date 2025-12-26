/** Wizard navigation buttons component. */

import React from "react";
import { Button } from "@/components/shared/Button";

interface WizardNavigationProps {
  currentStep: number;
  totalSteps: number;
  onNext: () => void;
  onBack: () => void;
  onCancel: () => void;
  onStartOver?: () => void;
  hasDraft?: boolean;
  isNextDisabled?: boolean;
  isSubmitting?: boolean;
  nextLabel?: string;
}

export const WizardNavigation: React.FC<WizardNavigationProps> = ({
  currentStep,
  totalSteps,
  onNext,
  onBack,
  onCancel,
  onStartOver,
  hasDraft = false,
  isNextDisabled = false,
  isSubmitting = false,
  nextLabel,
}) => {
  const isFirstStep = currentStep === 1;
  const isLastStep = currentStep === totalSteps;

  return (
    <div className="flex items-center justify-between pt-6 border-t border-gray-200">
      <div className="flex items-center gap-2">
        {!isFirstStep && (
          <Button variant="secondary" onClick={onBack} disabled={isSubmitting}>
            Back
          </Button>
        )}
        {(hasDraft || !isFirstStep) && onStartOver && (
          <Button
            variant="ghost"
            onClick={onStartOver}
            disabled={isSubmitting}
            className="text-gray-600 hover:text-gray-900"
          >
            Start Over
          </Button>
        )}
        <Button
          variant="ghost"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancel
        </Button>
      </div>
      <div>
        {isLastStep ? (
          <Button
            variant="primary"
            onClick={onNext}
            disabled={isNextDisabled || isSubmitting}
            isLoading={isSubmitting}
          >
            {nextLabel || "Create Agent"}
          </Button>
        ) : (
          <Button
            variant="primary"
            onClick={onNext}
            disabled={isNextDisabled || isSubmitting}
          >
            Next
          </Button>
        )}
      </div>
    </div>
  );
};


