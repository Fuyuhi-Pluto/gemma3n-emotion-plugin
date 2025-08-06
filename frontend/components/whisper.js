// ================== Whisper Messages ==================
const whisperMessages = {
  companion: [
    "🌿 I'm right here with you as you write.",
    "☁️ Every word you type is safe here.",
    "🫧 I’m here, listening quietly.",
    "🌙 Your thoughts can rest on this page.",
    "🍀 I'm staying with you through these words.",
    "🌸 Your feelings have company now.",
    "🕊️ Whatever you write, I’m here beside it.",
    "✨ This is your space, I’m just here to hold it with you.",
    "💖 These sentences are not alone, and neither are you.",
    "🌼 I’ll stay with every word until you’re done."
  ],
  acknowledgement: [
    "🌟 Thank you for sharing these thoughts.",
    "📖 Your words have meaning, even the small ones.",
    "🕯️ Writing this down is an act of care.",
    "🌿 Each line shows courage.",
    "💌 Your voice matters here.",
    "🍂 Noticing your feelings is already a step forward.",
    "🌸 Even a few words carry weight.",
    "✨ You’re giving shape to something real.",
    "🌼 Thank you for letting these feelings exist on paper.",
    "🫀 This page now carries a piece of your truth."
  ],
  guidance: [
    "🌊 Let the next thought flow naturally.",
    "🕊️ If it feels heavy, you can pause and keep breathing.",
    "🍂 Try finishing this sentence before moving on.",
    "🌱 Let your words grow slowly, no rush.",
    "💫 Notice which feeling is the strongest right now.",
    "🌼 If a memory comes up, let it land gently here.",
    "🎧 Listen to your inner voice, then write the next word.",
    "🌙 You can explore one thought a bit deeper.",
    "✨ Let your sentences wander where they want to go.",
    "🕯️ Take one more breath, then write what comes."
  ],
  encouragement: [
    "🌟 You’re doing beautifully, one line at a time.",
    "🍀 Your words are unfolding just right.",
    "🕊️ Keep going, your voice is strong here.",
    "💫 Even small reflections bring clarity.",
    "🌸 This page is brighter because of your words.",
    "🎉 Every word you write is a gentle step forward.",
    "🕯️ You’re giving yourself space to heal.",
    "🌼 Look how far you’ve come in just a few lines.",
    "✨ You’re honoring your feelings with every sentence.",
    "💖 This is your moment of self-kindness."
  ],
  interactive: [
    "🖊️ Circle a word that feels most important right now.",
    "🌊 Pause and reread the last sentence—how does it feel?",
    "🫀 Notice which word feels the heaviest or lightest.",
    "☁️ Take a tiny breath, then add one more thought.",
    "🎨 Imagine coloring your current feeling in your mind.",
    "🍂 Look at your words—pick one that surprises you.",
    "💫 Add a single word that captures your feeling best.",
    "🕊️ Touch the page or keyboard—feel your presence here.",
    "🌼 Reread a line and silently say: 'This is me today.'",
    "📖 If one sentence stands out, underline it softly."
  ]
};

// ================== Whisper Logic ==================
let whisperIndex = 0;
let whisperSequence = [];
const whisperCategories = ["companion", "acknowledgement", "guidance", "encouragement", "interactive"];

/**
 * 获取新的低语序列（按类别顺序各取 1-2 条）
 */
function getWhisperSequence() {
  const sequence = [];
  whisperCategories.forEach(cat => {
    const msgs = whisperMessages[cat];
    const count = Math.floor(Math.random() * 2) + 1; // 每类取 1-2 条
    const shuffled = msgs.slice().sort(() => 0.5 - Math.random());
    sequence.push(...shuffled.slice(0, count));
  });
  return sequence;
}

/**
 * 显示低语
 */
function showWhisper(el) {
  if (whisperIndex >= whisperSequence.length) {
    whisperSequence = getWhisperSequence();
    whisperIndex = 0;
  }

  const msg = whisperSequence[whisperIndex++];
  el.innerText = msg;
  el.classList.add("show");
  el.style.opacity = 1;

  setTimeout(() => {
    el.style.opacity = 0;
    el.classList.remove("show");
    el.innerText = "";
  }, 3500);
}

/**
 * 初始化低语循环
 * @param {string} inputId 输入框的ID
 * @param {string} whisperId 显示低语元素的ID
 */
function startWhisperCycle(inputId, whisperId) {
  const input = document.getElementById(inputId);
  const el = document.getElementById(whisperId);
  let hasWhispered = false;

  input.addEventListener('input', () => {
    if (!hasWhispered) {
      showWhisper(el);
      hasWhispered = true;
      setTimeout(() => hasWhispered = false, 4000);
    }
  });
}
