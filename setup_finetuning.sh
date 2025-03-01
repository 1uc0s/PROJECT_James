#!/bin/bash
# Script to set up Ollama fine-tuning for lab book generation

# Create necessary directories
mkdir -p finetuning/labbooks

# Create Modelfile with system prompt and template
cat > finetuning/Modelfile << EOL
FROM llama3.2

# System prompt to guide model behavior
SYSTEM """
You are LabBookAssistant, an AI specialized in creating concise, focused lab books.
Structure lab books with these sections:
1. Aims - What the lab session planned to accomplish
2. Choices - Key decisions made during the lab
3. Summary - Main discoveries and learnings
4. Questions - Areas needing further investigation

Keep language clear, scientific, and direct.
"""

# Template for formatting the training examples
TEMPLATE """
{{- if .System }}
<|im_start|>system
{{ .System }}<|im_end|>
{{- end }}

{{- if .Prompt }}
<|im_start|>user
{{ .Prompt }}<|im_end|>
{{- end }}

{{- if .Response }}
<|im_start|>assistant
{{ .Response }}<|im_end|>
{{- end }}
"""
EOL

# Create sample training example
cat > finetuning/labbooks/example1.json << EOL
{
  "prompt": "Create a lab book from this transcript: [You]: Today I'm conducting an experiment to measure the effect of temperature on enzyme activity. I'll be using catalase from potato extract and varying the temperature from 10°C to 50°C in 10-degree increments. I've set up a water bath for temperature control. [Lab Partner]: Remember to denature a sample as a negative control. [You]: Good point. I'll prepare a boiled sample too. I'm measuring reaction rate by the production of oxygen bubbles over 30 seconds. For the 20°C sample, I measured 3.2 mL of oxygen. At 30°C it increased to 5.7 mL. The 40°C sample produced 7.1 mL, but the 50°C sample only produced 2.3 mL. [Instructor]: Why do you think activity decreased at 50°C? [You]: I believe the enzyme is beginning to denature at this temperature, losing its tertiary structure. I chose to use potato extract because it's readily available and has high catalase activity. I'm wondering if different sources of catalase would show different temperature optima.",
  "response": "# Temperature Effects on Catalase Activity\n\n**Date:** 2025-03-01\n\n**Participants:** You, Lab Partner, Instructor\n\n## Aims\nTo investigate the effect of temperature on catalase enzyme activity using potato extract, specifically measuring activity across a temperature range of 10-50°C.\n\n## Choices\n- Used potato extract as catalase source due to its high enzyme content and availability\n- Selected temperature range of 10-50°C with 10-degree increments to observe both optimal and denaturing conditions\n- Measured enzyme activity by oxygen production (bubble volume) over a 30-second period\n- Included a boiled sample as a negative control to confirm enzyme denaturation\n\n## Summary\nThe catalase activity showed a clear temperature-dependent relationship. Activity increased with temperature from 10°C to 40°C, with the highest oxygen production (7.1 mL) observed at 40°C. Activity decreased significantly at 50°C (2.3 mL), suggesting enzyme denaturation begins at this temperature. This confirms that the enzyme has an optimal temperature range after which thermal denaturation causes loss of function.\n\n## Questions\n- Would different sources of catalase (from other organisms) show different temperature optima?\n- What is the precise temperature at which denaturation begins (between 40-50°C)?\n- How does pH interact with temperature effects on enzyme activity?\n- Could enzyme stabilizers or inhibitors shift the temperature response curve?"
}
EOL

# Create example 2
cat > finetuning/labbooks/example2.json << EOL
{
  "prompt": "Create a lab book from this transcript: [You]: I'm conducting a titration experiment to determine the concentration of an unknown acetic acid solution. I've calibrated the pH meter and prepared a standardized 0.1M NaOH solution. I'm using phenolphthalein as the indicator. [Lab Partner]: Make sure you record the initial buret reading before you start. [You]: Yes, I've recorded it as 0.00 mL. I'm adding the NaOH solution drop by drop while stirring. At around 18.5 mL, the solution started showing a faint pink color that disappeared quickly. By 24.2 mL, the pink color persisted for about 30 seconds. The endpoint was reached at 25.7 mL, with a stable pink color. I decided to repeat the experiment twice more for accuracy. The second trial endpoint was at 25.5 mL, and the third was at 25.6 mL. The consistent results indicate good precision. I used a 25 mL pipette to measure my acid sample, which was a decision I made to ensure I wouldn't exceed the buret capacity.",
  "response": "# Determination of Unknown Acetic Acid Concentration\n\n**Date:** 2025-03-01\n\n**Participants:** You, Lab Partner\n\n## Aims\nTo determine the concentration of an unknown acetic acid solution through acid-base titration with standardized NaOH.\n\n## Choices\n- Used a standardized 0.1M NaOH solution as the titrant\n- Selected phenolphthalein as the indicator for its appropriate pH range for acetic acid neutralization\n- Measured exactly 25 mL of the unknown acid solution to stay within buret capacity\n- Performed three titration trials to ensure precision and accuracy\n- Determined endpoint by persistent pink color rather than first appearance of color\n\n## Summary\nThe titration required an average of 25.6 mL of 0.1M NaOH to neutralize 25 mL of the unknown acetic acid solution. The endpoints were consistent across three trials (25.7, 25.5, and 25.6 mL), indicating good precision in the measurements. The titration curve showed characteristic weak acid behavior with a gradual color change beginning around 18.5 mL before reaching the permanent endpoint. Using the stoichiometric relationship between acetic acid and NaOH, the concentration of the unknown acetic acid solution can be calculated as approximately 0.102M.\n\n## Questions\n- How would the results differ if a different indicator had been used?\n- What is the effect of temperature on the titration endpoint of acetic acid?\n- Could the presence of other weak acids in the unknown solution affect the results?\n- Would an automated titrator provide more precise results than the manual titration method used?"
}
EOL

# Create example 3
cat > finetuning/labbooks/example3.json << EOL
{
  "prompt": "Create a lab book from this transcript: [You]: Today I'm investigating the diffraction pattern of laser light through different sized slits. I've set up a helium-neon laser with 632.8 nm wavelength, a set of single slits of various widths, and a screen at a distance of 2 meters. [Instructor]: Remember to record the width of each slit you use. [You]: I've noted them all down. I'm starting with the 0.1 mm slit. The diffraction pattern shows a bright central maximum with distinct minima and secondary maxima. I measured the distance between the first minima on either side as 12.6 cm. For the 0.05 mm slit, this distance increased to 25.3 cm, and for the 0.2 mm slit, it decreased to 6.2 cm. I decided to keep the laser power low to minimize any risk to our eyes, even though we're wearing safety goggles. I'm trying to determine if the formula d·sin(θ) = m·λ accurately predicts my observations, where d is the slit width.",
  "response": "# Single-Slit Diffraction Patterns of Laser Light\n\n**Date:** 2025-03-01\n\n**Participants:** You, Instructor\n\n## Aims\nTo investigate the relationship between slit width and diffraction pattern dimensions using a helium-neon laser, and verify the single-slit diffraction formula.\n\n## Choices\n- Used a helium-neon laser (632.8 nm wavelength) for its coherence and monochromatic properties\n- Selected three different slit widths (0.05 mm, 0.1 mm, and 0.2 mm) to observe width-dependent effects\n- Positioned the screen at 2 meters from the slits to obtain clear, measurable diffraction patterns\n- Kept laser power at a minimum level while wearing safety goggles to ensure eye safety\n- Measured the distance between first minima on either side of the central maximum as the key parameter\n\n## Summary\nThe diffraction patterns clearly demonstrated the inverse relationship between slit width and diffraction pattern spread. The 0.05 mm slit produced the widest pattern (25.3 cm between first minima), the 0.1 mm slit resulted in a medium spread (12.6 cm), and the 0.2 mm slit created the narrowest pattern (6.2 cm). These measurements show that when slit width is halved, the distance between minima approximately doubles, confirming the theoretical prediction. The observed values are consistent with the single-slit diffraction formula d·sin(θ) = m·λ, where the angle to the first minimum is given by sin(θ) = λ/d.\n\n## Questions\n- How would the diffraction pattern change if we used a laser with a different wavelength?\n- What effect would changing the distance to the screen have on our measurements and calculations?\n- How does the intensity distribution across the diffraction pattern relate to slit width?\n- Could we use this setup to accurately measure the wavelength of an unknown laser source?"
}
EOL

# Create script to build the custom model
cat > finetuning/build_model.sh << EOL
#!/bin/bash
set -e

echo "Building custom lab book model for Ollama..."

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
  echo "Error: Ollama is not running. Please start Ollama with 'ollama serve'"
  exit 1
fi

# Check if base model exists
if ! ollama list | grep -q llama3.2; then
  echo "Base model llama3.2 not found. Pulling from repository..."
  ollama pull llama3.2
fi

# Build the custom model
echo "Creating custom model 'labbook-custom'..."
ollama create labbook-custom -f finetuning/Modelfile

echo "Custom model 'labbook-custom' created successfully!"
echo "To use this model, update your config.py to set:"
echo "LLM_MODEL_PATH = \"ollama:labbook-custom\""
EOL

chmod +x finetuning/build_model.sh

# Create a script to generate lab books using the fine-tuned model
cat > finetuning/test_model.sh << EOL
#!/bin/bash
set -e

echo "Testing lab book generation with custom model..."

# Sample prompt
PROMPT="Create a lab book from this transcript: [You]: Today I measured the conductivity of different solutions. I tested salt water, sugar water, and tap water with a conductivity meter..."

# Use Ollama API to generate response
curl -s -X POST http://localhost:11434/api/generate -d "{
  \"model\": \"labbook-custom\",
  \"prompt\": \"\$PROMPT\",
  \"stream\": false
}" | jq -r '.response'

echo -e "\n\nTest complete. Add more training examples to finetuning/labbooks/ for better results."
EOL

chmod +x finetuning/test_model.sh

echo "
🧪 Fine-tuning setup complete! 🧪

To use the fine-tuning system:

1. Add more training examples to finetuning/labbooks/ directory
   - Follow the example format with 'prompt' and 'response' fields
   - Include at least 5-10 diverse examples for better results

2. Run './finetuning/build_model.sh' to create your custom model

3. Test the model with './finetuning/test_model.sh'

4. Update config.py to use your custom model:
   LLM_MODEL_PATH = \"ollama:labbook-custom\"

The more quality examples you provide, the better your lab book assistant will perform!
"