export const FLOWS = {

  diagnose: {
    label: "Diagnose an issue",
    description: "Step-by-step symptom checker",
    start: "appliance",
    steps: {
      appliance: {
        prompt: "What type of appliance are you having trouble with?",
        type: "buttons",
        options: [
          { label: "Refrigerator", next: "refrigerator" },
          { label: "Dishwasher",   next: "dishwasher"   },
        ],
      },
      refrigerator: {
        prompt: "What's the issue with your refrigerator?",
        type: "buttons",
        options: [
          { label: "Not cooling",      query: "My refrigerator is not cooling or staying cold" },
          { label: "Ice maker broken", query: "The ice maker on my refrigerator is not working" },
          { label: "Leaking water",    query: "My refrigerator is leaking water" },
          { label: "Making noise",     query: "My refrigerator is making loud or unusual noises" },
          { label: "Door not sealing", query: "My refrigerator door is not sealing properly" },
        ],
      },
      dishwasher: {
        prompt: "What's the issue with your dishwasher?",
        type: "buttons",
        options: [
          { label: "Not draining",    query: "My dishwasher is not draining, water pooling at bottom" },
          { label: "Dishes not clean", query: "My dishwasher is not cleaning dishes properly" },
          { label: "Won't start",     query: "My dishwasher won't start or turn on" },
          { label: "Leaking water",   query: "My dishwasher is leaking water" },
          { label: "Making noise",    query: "My dishwasher is making loud or unusual noises" },
        ],
      },
    },
  },

  modelLookup: {
    label: "Find parts by model",
    description: "Enter your model to see all compatible parts",
    start: "model",
    steps: {
      model: {
        prompt: "Enter your appliance model number",
        type: "input",
        placeholder: "e.g. WDT780SAEM1",
        inputKey: "model",
        queryFn: (v) => `What parts are compatible with model ${v.model}?`,
      },
    },
  },

  compatibility: {
    label: "Check compatibility",
    description: "Check if a part fits your appliance",
    start: "part",
    steps: {
      part: {
        prompt: "Enter the part number you want to check",
        type: "input",
        placeholder: "e.g. PS11752778",
        inputKey: "part",
        next: "model",
      },
      model: {
        prompt: "Enter your appliance model number",
        type: "input",
        placeholder: "e.g. WDT780SAEM1",
        inputKey: "model",
        queryFn: (v) => `Is part ${v.part} compatible with model ${v.model}?`,
      },
    },
  },

  browse: {
    label: "Browse parts",
    description: "Browse parts by appliance and category",
    start: "appliance",
    steps: {
      appliance: {
        prompt: "Which appliance do you want to browse parts for?",
        type: "buttons",
        options: [
          { label: "Refrigerator", next: "refrigerator" },
          { label: "Dishwasher",   next: "dishwasher"   },
        ],
      },
      refrigerator: {
        prompt: "Which category of refrigerator parts?",
        type: "buttons",
        options: [
          { label: "Ice maker parts", query: "Show me ice maker parts for refrigerators" },
          { label: "Door & hinges",   query: "Show me refrigerator door and hinge parts" },
          { label: "Water system",    query: "Show me refrigerator water inlet valves and water line parts" },
          { label: "Cooling & fans",  query: "Show me refrigerator evaporator and condenser fan parts" },
          { label: "Drawers & bins",  query: "Show me refrigerator drawers, shelves, and door bins" },
        ],
      },
      dishwasher: {
        prompt: "Which category of dishwasher parts?",
        type: "buttons",
        options: [
          { label: "Pumps & motors",  query: "Show me dishwasher pump and motor parts" },
          { label: "Spray arms",      query: "Show me dishwasher spray arm parts" },
          { label: "Door & latch",    query: "Show me dishwasher door latch and gasket parts" },
          { label: "Heating element", query: "Show me dishwasher heating element parts" },
          { label: "Racks & baskets", query: "Show me dishwasher racks and baskets" },
        ],
      },
    },
  },

  orderLookup: {
    label: "Order status",
    description: "Track an existing order",
    start: "orderId",
    steps: {
      orderId: {
        prompt: "Enter your order ID",
        type: "input",
        placeholder: "e.g. ORD-001",
        inputKey: "orderId",
        queryFn: (v) => `What is the status of order ${v.orderId}?`,
      },
    },
  },

};
