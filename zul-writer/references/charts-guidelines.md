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
* Mainly use https://www.zkoss.org/javadoc/latest/zkcharts/org/zkoss/chart/Series.html to provide sample data. (Since it works without checking a chart type)
* In most cases, don't specify `width` attributes since it's `100%` by default and fill its parent container.