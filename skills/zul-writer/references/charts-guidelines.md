# ZK Charts Guidelines

When the ZUL page requires a `<charts>` component, go through these steps **before** generating any chart-related ZUL code.

## Dependency Check

1. **Check the build file** — look for the `zkcharts` dependency in the project's `pom.xml` or `build.gradle`:

   ```xml
   <dependency>
       <groupId>org.zkoss.chart</groupId>
       <artifactId>zkcharts</artifactId>
       <version>${zkcharts.version}</version>
   </dependency>
   ```
Notice that zkcharts has different version with zk. Check https://mavensync.zkoss.org/eval/org/zkoss/chart/zkcharts/ for the latest version.

2. **If the dependency is missing** — ask the user whether they want to add it before continuing.

3. **If the user declines** — drop the chart requirement entirely. Do not use `<charts>` anywhere in the generated ZUL; find an alternative or omit the chart section.

4. **If the user agrees** — proceed with `<charts>` in the ZUL output.

## Providing Sample Data

**Which route depends on the pattern, and the two are not interchangeable.**

* **MVC (Composer)** — use [`Series`](https://www.zkoss.org/javadoc/latest/zkcharts/org/zkoss/chart/Series.html)
  on the wired `Charts` object. It works without checking the chart type, which is why it is the
  default advice for a Composer.
* **MVVM (ViewModel)** — `Series` is not reachable. The binder's only entry point into a chart is
  `model="@load(vm.revenueModel)"`, so the ViewModel returns a `ChartsModel`:
  * `DefaultCategoryModel` — line, area, column, bar. `setValue(series, category, number)`.
  * `DefaultPieModel` — pie and donut. `setValue(category, number)`, inherited from
    `DefaultSingleValueCategoryModel`.
  * A donut is a pie plus `PiePlotOptions.setInnerSize("70%")`.

  Writing a Composer's `Series` code into a ViewModel produces a chart that compiles, renders
  empty, and reports nothing — there is no error to read, because nothing asked the binder for
  anything.

**A chart is the one exception to "Step 4 holds behaviour, not data".** `<charts>` has no literal
form, so its data belongs in the controller from the first render while the rest of the page still
goes through the literal pass. See *A chart has no Pass 1* in Step 2.

* In most cases, don't specify `width` attributes since it's `100%` by default and fill its parent container.