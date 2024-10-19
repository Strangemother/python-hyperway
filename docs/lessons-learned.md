# Historical builds

Although many existing libraries cater to graph theory, they often require a deep understanding of complex terminology and concepts. As an engineer without formal training in graph theory, these libraries are challenging.
**Hyperway** is the result of few years of research aimed at developing a simplified functional graph-based execution library with a minimal set of core features.

I'm slowly updating it to include the more advanced [future features](docs/future.md), such as hyper-edges and connection-decisions, bridging the gap between academic graph theory and practical application, providing developers with a low-level runtime that facilitates functional execution without the need for specialized knowledge.

The core components of Hyperway were developed through more than 40 rewrites and refinements, leading to a robust framework that supports both procedural and parallel functionality with the same homogeneous interface.


**Lessons Learned**

Each restart was a lesson in what _not-to-do_. I have fundamentally 25 restart/rewrites. Roughly three of them I'd consider "complete" enough to function within a range of distinct cases, such as "electronic circuit", "logic gates", "function chains" and a bunch of other variants.

1. API/Libraries Servers/Websites/Render-loops - bin-em
   First version was an all-singing socketed executor. Which was crap to maintain.
2. Let's try plugging-up _Devices_ and _pipes_
   It works, But then I also have plugin functions, `on` method, mixins and all sorts of 'library' bits pushing around objects. It's too limited.
3. The same thing; but with a "system" running a super-loop of futures
   Sure it works, but now we have an asyncio execution machine, with a bunch of mixins, structures classes, and a specific _run_ function.
   Entities are too classy, with a large unwanted method stack - more simpler is required
