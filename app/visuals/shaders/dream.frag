#version 330

uniform float u_time;
uniform vec2 u_resolution;
uniform float u_intensity;
uniform float u_distortion;

out vec4 fragColor;

float hash(vec2 p)
{
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float noise(vec2 p)
{
    vec2 i = floor(p);
    vec2 f = fract(p);

    f = f * f * (3.0 - 2.0 * f);

    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));

    return mix(
        mix(a, b, f.x),
        mix(c, d, f.x),
        f.y
    );
}

float fbm(vec2 p)
{
    float value = 0.0;
    float amplitude = 0.5;

    for (int i = 0; i < 5; i++)
    {
        value += amplitude * noise(p);
        p *= 2.0;
        amplitude *= 0.5;
    }

    return value;
}

void main()
{
    vec2 uv = gl_FragCoord.xy / u_resolution.xy;

    // Correct for the window's aspect ratio.
    vec2 p = uv - 0.5;
    p.x *= u_resolution.x / u_resolution.y;

    float t = u_time * 0.18;
    float distortion = u_distortion;

    // Slowly deform the space itself.
    vec2 q = p;

    q += 0.18 * distortion * vec2(
        sin(q.y * 3.0 + t),
        cos(q.x * 3.0 - t)
    );

    float n = fbm(q * 2.4 + vec2(t, -t * 0.7));

    // Flowing wave structures.
    float waves =
        sin(q.x * 5.0 + n * 5.0 - t * 2.0) *
        cos(q.y * 4.0 - n * 4.0 + t);

    // Radial form.
    float radius = length(q);
    float ring = sin(radius * 18.0 - t * 3.0 + n * 6.0);

    // Combine the structures.
    float field = n * 0.65 + waves * 0.22 + ring * 0.13;

    // Soft center illumination.
    float glow = exp(-radius * 2.8);

    // Convert the mathematical field into a visual gradient.
    float r = 0.5 + 0.5 * sin(field * 3.0 + t);
    float g = 0.5 + 0.5 * sin(field * 3.0 + t + 2.0);
    float b = 0.5 + 0.5 * sin(field * 3.0 + t + 4.0);

    vec3 color = vec3(r, g, b);

    // Add depth-like illumination.
    color *= (0.35 + glow * 1.25) * u_intensity;

    // Subtle flowing brightness.
    color += vec3(0.08) * pow(max(field, 0.0), 2.0);

    fragColor = vec4(color, 1.0);
}