# Miro Canvas - 3 Divergent Prototypes

A minimal prototype showcasing three different technical approaches to building an infinite canvas like Miro.

## Live Demo

Open `index.html` in a browser to see all three prototypes side-by-side.

## The Three Approaches

### 1. SVG Transform
- **Technology**: Scalable Vector Graphics with viewBox manipulation
- **Strengths**: Infinite precision, native DOM events, great for diagrams
- **Use Case**: When you need vector graphics and resolution independence
- **Pan/Zoom**: Manipulates SVG viewBox coordinates

### 2. Canvas API
- **Technology**: HTML5 Canvas with 2D rendering context
- **Strengths**: High performance, pixel-level control, great for animations
- **Use Case**: When you need maximum rendering performance
- **Pan/Zoom**: Camera transform applied to all draw calls

### 3. CSS Transform
- **Technology**: DOM elements with CSS transforms
- **Strengths**: Leverage HTML/CSS, easy styling, native browser features
- **Use Case**: When you need rich HTML content and interactions
- **Pan/Zoom**: CSS transform on container element

## Features

Each prototype includes:
- **Pan**: Drag the canvas background to move around
- **Zoom**: Mouse wheel to zoom in/out
- **Draggable Elements**: Move items around the canvas

## Technical Comparison

| Feature | SVG | Canvas | DOM/CSS |
|---------|-----|--------|---------|
| Performance | Medium | High | Low-Medium |
| Scalability | Excellent | Good | Medium |
| Styling | CSS/Attributes | Manual | Full CSS |
| Hit Detection | Native | Manual | Native |
| Text Rendering | Excellent | Good | Excellent |
| Memory Usage | High | Low | Very High |

## Running Locally

Simply open `index.html` in any modern browser. No build process required.
