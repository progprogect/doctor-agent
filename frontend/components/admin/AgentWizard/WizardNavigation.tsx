/** Wizard navigation buttons component. */

import React from "react";
import { Button } from "@/components/shared/Button";

interface WizardNavigationProps {
  currentStep: number;
  totalSteps: number;
  onNext: () => void;
  onBack: () => void;
  onCancel: () => void;
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
  isNextDisabled = false,
  isSubmitting = false,
  nextLabel,
}) => {
  const isFirstStep = currentStep === 1;
  const isLastStep = currentStep === totalSteps;

  return (
    <div className="flex items-center justify-between pt-6 border-t border-gray-200">
      <div>
        {!isFirstStep && (
          <Button variant="secondary" onClick={onBack} disabled={isSubmitting}>
            Back
          </Button>
        )}
        <Button
          variant="ghost"
          onClick={onCancel}
          disabled={isSubmitting}
          className="ml-2"
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


