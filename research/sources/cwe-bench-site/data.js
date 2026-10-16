window.CWEB_DATA_V0 = {
  models: ["Fable 5", "GPT-5.6", "Gemini 3.7 Flash", "Opus 4.8", "Grok 4.6", "Qwen 3.8 Max", "HY4", "GLM 5.3", "DeepSeek V4 Flash", "Muse Spark 1.2", "MiniMax M3", "Kimi K3", "Nemotron 3 Ultra", "Inkling"],
  nTasks: 100,

  /* Rows ordered by the leader's deterministic pass rate, highest first. */
  language: {
    categories: ['C/C++', 'Go', 'Java', 'JS/TS', 'Python', 'Rust'],
    values: {
      'Fable 5': [ 45,  34,  44,  61,  71,  33],
      'GPT-5.6': [ 45,  32,  40,  57,  31,  25],
      'Gemini 3.7 Flash': [ 45,  35,  35,  64,  54,   0],
      'Opus 4.8': [ 35,  24,  38,  60,  29,  33],
      'Grok 4.6': [ 35,  15,  28,  68,  50,   0],
      'Qwen 3.8 Max': [ 42,  10,  15,  66,  33,   0],
      'HY4': [ 35,  10,  22,  59,  58,   0],
      'GLM 5.3': [ 35,   9,  25,  53,  50,  25],
      'DeepSeek V4 Flash': [ 25,  15,  20,  53,  19,   0],
      'Muse Spark 1.2': [ 26,   5,  25,  70,  17,   0],
      'MiniMax M3': [ 19,   8,  17,  43,  25,   0],
      'Kimi K3': [ 19,   5,  22,  41,   0,   0],
      'Nemotron 3 Ultra': [ 19,   0,  17,  36,  33,   0],
      'Inkling': [ 10,   5,  11,  25,  17,   0],
    }
  },

  owasp: {
    models: ['Fable 5', 'GPT-5.6', 'Gemini 3.7 Flash', 'Opus 4.8', 'Grok 4.6', 'Qwen 3.8 Max', 'HY4', 'GLM 5.3', 'DeepSeek V4 Flash', 'Muse Spark 1.2', 'MiniMax M3', 'Kimi K3', 'Nemotron 3 Ultra', 'Inkling'],
    categories: ['A01', 'A02', 'A03', 'A04', 'A05', 'A06', 'A07', 'A08', 'A09', 'A10'],
    names: {
      A01: 'Broken Access Control',
      A02: 'Security Misconfiguration',
      A03: 'Software Supply Chain Failures',
      A04: 'Cryptographic Failures',
      A05: 'Injection',
      A06: 'Insecure Design',
      A07: 'Authentication Failures',
      A08: 'Software or Data Integrity Failures',
      A09: 'Security Logging and Alerting Failures',
      A10: 'Mishandling of Exceptional Conditions',
    },
    values: {
      'Fable 5': [ 50,  68,  58,  61,  55,  41,  30,  28,  42,  43],
      'GPT-5.6': [ 49,  42,  42,  70,  59,  44,  20,  25,  28,  44],
      'Gemini 3.7 Flash': [ 62,  39,  45,  52,  39,  38,  39,  22,  58,  48],
      'Opus 4.8': [ 45,  67,  42,  59,  41,  28,  25,  22,  38,  18],
      'Grok 4.6': [ 70,  67,  50,  18,  36,  25,   9,  22,  40,  36],
      'Qwen 3.8 Max': [ 50,  53,  57,  40,  38,  12,  14,  20,  45,  14],
      'HY4': [ 40,  44,  50,  41,  64,  12,   9,   0,  30,  36],
      'GLM 5.3': [ 28,  53,  60,  34,  36,  25,   3,  19,  38,  28],
      'DeepSeek V4 Flash': [ 12,  47,  38,  33,  38,  19,  14,  19,  29,  23],
      'Muse Spark 1.2': [ 20,  67,  40,  45,  32,  38,   9,  22,  30,   5],
      'MiniMax M3': [ 22,  39,  38,  22,  21,  16,   9,  11,  35,   2],
      'Kimi K3': [ 10,  33,  40,   9,  27,  25,   9,  22,  20,   9],
      'Nemotron 3 Ultra': [ 20,  44,  30,  45,   9,  12,   0,  11,  20,   0],
      'Inkling': [  0,  30,  23,  28,   5,  12,   0,   6,  25,   0],
    }
  },

  cost: {
    points: [
      { model: 'Fable 5', cost: 10.27, pass1: 47.8, family: 'closed' },
      { model: 'GPT-5.6', display: 'GPT-5.6-sol', cost: 2.29, pass1: 44.2, family: 'closed' },
      { model: 'Gemini 3.7 Flash', cost: 1.43, pass1: 44.0, family: 'closed' },
      { model: 'Opus 4.8', cost: 2.43, pass1: 42.0, family: 'closed' },
      { model: 'Grok 4.6', cost: 1.77, pass1: 38.2, family: 'closed' },
      { model: 'Qwen 3.8 Max', cost: 1.45, pass1: 37.5, family: 'openrouter' },
      { model: 'HY4', cost: 0.75, pass1: 33.8, family: 'openrouter' },
      { model: 'GLM 5.3', cost: 1.86, pass1: 31.1, family: 'openrouter' },
      { model: 'DeepSeek V4 Flash', cost: 0.13, pass1: 30.4, family: 'openrouter' },
      { model: 'Muse Spark 1.2', cost: 2.09, pass1: 30.3, family: 'openrouter' },
      { model: 'MiniMax M3', cost: 0.69, pass1: 22.7, family: 'openrouter' },
      { model: 'Kimi K3', cost: 1.18, pass1: 22.5, family: 'openrouter' },
      { model: 'Nemotron 3 Ultra', cost: 1.17, pass1: 18.5, family: 'openrouter' },
      { model: 'Inkling', cost: 1.76, pass1: 15.6, family: 'openrouter' },
    ],
    note: 'Cost is the average billed API spend for one rollout on one task. All pass rates are deterministic (programmatic == 1). Open-weight models run through opencode on OpenRouter and are shown only at >=95% graded coverage.'
  }
};
