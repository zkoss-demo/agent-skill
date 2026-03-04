# ZK Charts Dependency Check

When the ZUL page requires a `<charts>` component, go through these steps **before** generating any chart-related ZUL code.

## Steps

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
