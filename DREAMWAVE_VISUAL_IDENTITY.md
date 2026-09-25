# DreamWave Visual Identity v0.1

## 1. Core Definition

**DreamWave is a living visual instrument that translates music into visual expression rather than merely displaying audio data.**

DreamWave should feel as though the music is giving life to something that exists within the visual space.

The goal is not to create a traditional audio visualizer that simply makes shapes react to frequencies.

The goal is to create a system where music has:

* physical presence
* emotion
* movement
* atmosphere
* moments of tension and release
* subtlety
* chaos
* order
* continuity

DreamWave should be capable of making different songs feel like different experiences.

---

## 2. The Fundamental Principle

### Music determines WHAT is happening.

### Visual expression determines HOW it happens.

Audio analysis should provide meaningful information about the music.

Visual modes should interpret that information differently.

Therefore:

**Audio analysis ≠ visual style.**

A change in visual style should not require rebuilding the audio system.

Likewise, improving audio analysis should benefit every visual mode.

---

# 3. DreamWave's Visual Anatomy

DreamWave's primary musical elements are currently understood as four expressive forces.

## Bass — The Heart

Bass is the driving force.

It is the heart of DreamWave.

Bass should generally feel:

* physical
* grounded
* bouncy
* powerful
* foundational
* emotional

Bass may become overwhelming or heartbreaking, but it can also become extremely subtle.

Bass should drive the experience without consuming it.

It must leave room for the other musical elements to exist.

Bass represents the relationship between:

**chaos and order**

and between:

**power and restraint.**

Where appropriate, continuous bass energy may create foundational motion while bass transients may create physical pulses or impacts.

---

## Mids — The Body

Mids represent DreamWave's body.

They are its:

* hands
* face
* gestures
* movement
* expression
* physical interaction with the music

Mids should not be restricted to a single behavior.

Depending on the music and visual mode, mids may:

* flow
* dance
* gesture
* distort
* form structures
* create movement
* become chaotic
* create recognizable expression

Mids are where DreamWave can appear to **express itself**.

---

## Highs — The Aura

High frequencies represent the ethereal character of music.

They are DreamWave's:

* sparkle
* sizzle
* rain
* particles
* atmosphere
* light
* energy
* fine detail

Highs can be:

* delicate
* beautiful
* fast
* slow
* sharp
* blinding
* exciting
* scrambled
* subtle

High-frequency expression should not be treated as merely decorative noise.

It represents an important emotional and atmospheric layer of the music.

---

## Impact — The Moment

Impact represents events rather than continuous behavior.

Impact is the:

**surprise.**

It is the moment when DreamWave suddenly changes.

An impact may:

* explode
* flash
* distort
* shockwave
* disrupt
* reorganize
* collapse into order
* create temporary chaos
* trigger another visual behavior

Impact should feel immediate.

It may:

* happen instantly and disappear
* decay naturally
* stop abruptly
* return again later with greater intensity

Repeated impacts should be capable of creating anticipation and release.

Impact is one of the primary mechanisms through which DreamWave can communicate the emotional structure of a song.

---

# 4. Silence

Silence does not automatically mean that DreamWave stops existing.

DreamWave should understand different kinds of quiet.

### Short silence

DreamWave may continue to:

* breathe
* drift
* settle
* hold its form
* remain subtly alive

### Extended silence

DreamWave may gradually become:

* still
* quiet
* mysterious
* dormant
* nearly motionless

### Sound returning

DreamWave should respond naturally and immediately when music returns.

A silence followed by sound should feel like:

**awakening rather than restarting.**

---

# 5. Music Without Percussion

DreamWave must not depend upon drums or obvious rhythmic beats to remain expressive.

A song may consist primarily of:

* vocals
* strings
* piano
* wind instruments
* ambient sound
* sustained tones
* acoustic instruments
* unusual or experimental sounds

These should still be capable of producing meaningful visual expression.

DreamWave should respond to the **character of the music**, not merely its percussion.

A song without drums should not feel like a broken version of a song with drums.

It should feel different.

---

# 6. Visual Modes

DreamWave should support multiple visual modes.

A mode determines the visual language through which musical information is expressed.

Initial experimental modes may include:

### Flow

Organic, liquid, continuous movement.

### Pulse

Heart-like, expanding and contracting, physically driven.

### Dance

Gestural, expressive, body-like movement.

### Ethereal

Atmospheric, luminous, delicate, particle-like, dreamlike.

### Chaos

Explosive, unstable, distorted, unpredictable, rapidly reorganizing.

These are starting concepts rather than final implementations.

Additional modes may be introduced later.

---

# 7. Mode Selection

Visual modes should eventually support two mechanisms.

## Manual Mode Selection

The user may cycle through available visual modes.

This allows the listener to decide how they want to experience a song.

## Automatic Mode Selection

DreamWave may eventually recognize changes in the music and select or transition toward an appropriate visual mode.

Automatic selection should not simply be random.

Future selection may consider characteristics such as:

* energy
* tempo
* dynamics
* spectral character
* rhythmic activity
* sustained vs transient sound
* musical density
* instrumentation

Automatic mode selection is a future capability, not a requirement for the first implementation.

---

# 8. Mode Independence

Visual modes must not become separate audio systems.

The underlying musical information should remain shared.

Conceptually:

Audio Capture
↓
Audio Analysis
↓
Musical Features
↓
DreamWave Expression
↓
Visual Mode
↓
Renderer
↓
Shader / Visual Output

A new visual mode should primarily change **interpretation**, not duplicate the audio-analysis pipeline.

---

# 9. Emotional Range

DreamWave should not always attempt to look beautiful, energetic, or impressive.

It should be capable of:

* beauty
* calm
* tension
* excitement
* chaos
* sadness
* mystery
* intensity
* restraint
* wonder

A visually quiet moment can be as important as an explosive one.

The system should preserve contrast.

**If everything is intense, nothing feels intense.**

---

# 10. Emergent Expression

DreamWave should not be reduced to a collection of fixed reactions such as:

> bass = grow
> mids = move
> highs = sparkle

Those relationships are useful starting points, but they are not the final identity.

The same musical feature may produce different visual behavior depending on:

* the current visual mode
* recent musical history
* surrounding energy
* transient events
* silence
* accumulated visual state

DreamWave should therefore be capable of **expression that develops over time**.

---

# 11. Continuity

DreamWave should feel continuous rather than repeatedly resetting every audio frame.

Visual state may persist through:

* musical phrases
* short silences
* repeated impacts
* transitions between energy levels
* changes in musical texture

The visual system should be capable of remembering enough recent state to make transitions feel natural.

---

# 12. Human Experience Comes First

Technical correctness is necessary but insufficient.

A parameter can be mathematically correct while producing an uninspiring visual result.

DreamWave development should therefore use two forms of validation:

### Engineering validation

Does the system behave correctly?

### Experiential validation

Does it **feel** like DreamWave?

Both matter.

A technically successful feature that makes the experience worse should be reconsidered.

---

# 13. Extensibility

DreamWave should be designed so that future visual expression can grow without requiring the entire system to be rebuilt.

Potential future capabilities include:

* additional visual modes
* mode transitions
* automatic mode selection
* richer musical features
* phrase detection
* musical-section awareness
* instrument-aware behavior
* persistent visual state
* generative visual forms
* multiple simultaneous visual layers
* user-created modes

These possibilities should not prematurely dictate the architecture.

Build only what current evidence requires.

---

# 14. Current Development Principle

DreamWave v0.1 is an exploration, not a finished visual language.

The purpose of the first implementation is to discover which combinations of:

**music → expression → visual behavior**

actually produce the intended experience.

Therefore:

**Prototype before committing to complexity.**

A successful experiment should influence the architecture.

A failed experiment should be allowed to fail without forcing the entire system to accommodate it.

---

# 15. DreamWave in One Sentence

> **DreamWave is a living visual instrument where music becomes movement, atmosphere, emotion, and moment — with the ability to express the same musical soul through different visual forms.**
