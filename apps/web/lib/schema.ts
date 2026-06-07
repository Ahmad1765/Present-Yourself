// Mirror of apps/api/app/schemas/slide.py — kept in sync via CI parity check.
import { z } from "zod";

export const SlideType = z.enum([
  "title",
  "section_header",
  "bullet_list",
  "two_column",
  "image_caption",
  "quote",
  "stat_callout",
  "comparison_table",
  "chart_placeholder",
  "closing",
]);
export type SlideType = z.infer<typeof SlideType>;

export const ElementKind = z.enum([
  "text",
  "bullets",
  "image",
  "shape",
  "table",
  "chart_placeholder",
]);

export const TextStyle = z
  .object({
    size: z.number().int().optional(),
    color: z.string().optional(),
    align: z.enum(["left", "center", "right"]).optional(),
    weight: z.number().int().optional(),
    italic: z.boolean().default(false),
  })
  .strict();

export const Element = z
  .object({
    id: z.string(),
    kind: ElementKind,
    role: z.string().nullable().optional(),
    content: z.string().nullable().optional(),
    items: z.array(z.string()).nullable().optional(),
    style: TextStyle.nullable().optional(),
    source: z.record(z.any()).nullable().optional(),
    candidates: z.array(z.record(z.any())).nullable().optional(),
    alt: z.string().nullable().optional(),
  })
  .strict();
export type Element = z.infer<typeof Element>;

export const Slide = z
  .object({
    id: z.string(),
    type: SlideType,
    layout_hint: z.string().nullable().optional(),
    elements: z.array(Element),
    notes: z.string().nullable().optional(),
    citations: z.array(z.string()).default([]),
  })
  .strict();
export type Slide = z.infer<typeof Slide>;

export const Palette = z
  .object({
    background: z.string().default("#FFFFFF"),
    foreground: z.string().default("#0F172A"),
    accent1: z.string().default("#2563EB"),
    accent2: z.string().default("#0EA5E9"),
    accent3: z.string().default("#F59E0B"),
    muted: z.string().default("#64748B"),
  })
  .strict();

export const FontSpec = z
  .object({ family: z.string().default("Inter"), weight: z.number().int().default(400) })
  .strict();

export const Fonts = z
  .object({
    heading: FontSpec.default({ family: "Inter", weight: 700 }),
    body: FontSpec.default({ family: "Inter", weight: 400 }),
  })
  .strict();

export const Dimensions = z
  .object({
    width_emu: z.number().int().default(12192000),
    height_emu: z.number().int().default(6858000),
    aspect: z.enum(["16:9", "4:3", "16:10"]).default("16:9"),
  })
  .strict();

export const DesignTokens = z
  .object({
    dimensions: Dimensions.default({ width_emu: 12192000, height_emu: 6858000, aspect: "16:9" }),
    palette: Palette.default({
      background: "#FFFFFF",
      foreground: "#0F172A",
      accent1: "#2563EB",
      accent2: "#0EA5E9",
      accent3: "#F59E0B",
      muted: "#64748B",
    }),
    fonts: Fonts.default({
      heading: { family: "Inter", weight: 700 },
      body: { family: "Inter", weight: 400 },
    }),
    logo: z
      .object({
        url: z.string(),
        position: z.enum(["top-left", "top-right", "bottom-left", "bottom-right"]).default("top-right"),
      })
      .strict()
      .nullable()
      .optional(),
  })
  .strict();
export type DesignTokens = z.infer<typeof DesignTokens>;

export const Citation = z
  .object({
    id: z.string(),
    url: z.string(),
    title: z.string(),
    publisher: z.string().nullable().optional(),
    snippet: z.string().nullable().optional(),
    fetched_at: z.string().nullable().optional(),
  })
  .strict();

export const Deck = z
  .object({
    id: z.string(),
    title: z.string(),
    language: z.string().default("en"),
    design_tokens: DesignTokens,
    slides: z.array(Slide),
    citations: z.array(Citation).default([]),
  })
  .strict();

export const SlideBlueprint = z
  .object({
    schema_version: z.literal("1.0").default("1.0"),
    deck: Deck,
  })
  .strict();
export type SlideBlueprint = z.infer<typeof SlideBlueprint>;
