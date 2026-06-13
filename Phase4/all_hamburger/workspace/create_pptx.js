const pptxgen = require('pptxgenjs');
const html2pptx = require('/Users/yeong/.claude/plugins/cache/anthropic-agent-skills/example-skills/69c0b1a06741/skills/pptx/scripts/html2pptx');
const path = require('path');

async function createPresentation() {
    const pptx = new pptxgen();
    pptx.layout = 'LAYOUT_16x9';
    pptx.author = 'KNU Mini Project';
    pptx.title = '기후변화가 햄버거 재료에 미치는 영향 분석';
    pptx.subject = 'FAOSTAT & Kaggle 공공데이터 기반 통계 분석';

    const workDir = '/Users/yeong/00_work_out/01_KNU/main_class/MINI_Project/pase4/hamburger/workspace';

    // Slide 1: Title
    await html2pptx(path.join(workDir, 'slide01_title.html'), pptx);

    // Slide 2: Project Overview
    await html2pptx(path.join(workDir, 'slide02_intro.html'), pptx);

    // Slide 3: Data Preprocessing
    await html2pptx(path.join(workDir, 'slide03_data.html'), pptx);

    // Slide 4: Temperature Trend with chart
    const { slide: slide4, placeholders: ph4 } = await html2pptx(path.join(workDir, 'slide04_temp.html'), pptx);
    if (ph4.length > 0) {
        slide4.addChart(pptx.charts.LINE, [{
            name: "Global Temperature Anomaly",
            labels: ["1990", "1995", "2000", "2005", "2010", "2015", "2019"],
            values: [0.64, 0.76, 0.64, 0.90, 1.02, 1.32, 1.47]
        }], {
            ...ph4[0],
            showTitle: true,
            title: 'Global Temperature Anomaly (°C)',
            titleFontSize: 11,
            showLegend: false,
            lineSize: 3,
            lineSmooth: true,
            showCatAxisTitle: true,
            catAxisTitle: 'Year',
            showValAxisTitle: true,
            valAxisTitle: 'Temperature Anomaly (°C)',
            valAxisMinVal: 0.5,
            valAxisMaxVal: 1.6,
            chartColors: ["E07A5F"]
        });
    }

    // Slide 5: Production Trends with chart
    const { slide: slide5, placeholders: ph5 } = await html2pptx(path.join(workDir, 'slide05_production.html'), pptx);
    if (ph5.length > 0) {
        slide5.addChart(pptx.charts.BAR, [{
            name: "Production Growth (%)",
            labels: ["Cucumbers", "Tomatoes", "Lettuce", "Wheat", "Potatoes", "Beef"],
            values: [94.2, 67.3, 58.9, 47.8, 32.4, 23.7]
        }], {
            ...ph5[0],
            barDir: 'bar',
            showTitle: true,
            title: 'Production Growth 2000-2023 (%)',
            titleFontSize: 11,
            showLegend: false,
            showCatAxisTitle: false,
            showValAxisTitle: true,
            valAxisTitle: 'Growth (%)',
            valAxisMinVal: 0,
            valAxisMaxVal: 100,
            chartColors: ["87A96B"]
        });
    }

    // Slide 6: Correlation Analysis with chart
    const { slide: slide6, placeholders: ph6 } = await html2pptx(path.join(workDir, 'slide06_correlation.html'), pptx);
    if (ph6.length > 0) {
        slide6.addChart(pptx.charts.BAR, [{
            name: "Pearson r",
            labels: ["Cucumbers", "Lettuce", "Tomatoes", "Wheat", "Beef", "Potatoes"],
            values: [0.77, 0.77, 0.76, 0.73, 0.72, 0.56]
        }], {
            ...ph6[0],
            barDir: 'bar',
            showTitle: true,
            title: 'Correlation with Temperature (Pearson r)',
            titleFontSize: 11,
            showLegend: false,
            showCatAxisTitle: false,
            showValAxisTitle: true,
            valAxisTitle: 'Correlation (r)',
            valAxisMinVal: 0,
            valAxisMaxVal: 1.0,
            chartColors: ["E07A5F"]
        });
    }

    // Slide 7: Regression Analysis with chart
    const { slide: slide7, placeholders: ph7 } = await html2pptx(path.join(workDir, 'slide07_regression.html'), pptx);
    if (ph7.length > 0) {
        slide7.addChart(pptx.charts.BAR, [{
            name: "R-squared",
            labels: ["Lettuce", "Tomatoes", "Wheat", "Beef", "Potatoes"],
            values: [0.593, 0.581, 0.535, 0.523, 0.312]
        }], {
            ...ph7[0],
            barDir: 'col',
            showTitle: true,
            title: 'Regression R² (Explanatory Power)',
            titleFontSize: 11,
            showLegend: false,
            showCatAxisTitle: true,
            catAxisTitle: 'Ingredient',
            showValAxisTitle: true,
            valAxisTitle: 'R²',
            valAxisMinVal: 0,
            valAxisMaxVal: 0.7,
            chartColors: ["87A96B"]
        });
    }

    // Slide 8: Extreme Weather Events
    await html2pptx(path.join(workDir, 'slide08_events.html'), pptx);

    // Slide 9: Korea Import Dependency with chart
    const { slide: slide9, placeholders: ph9 } = await html2pptx(path.join(workDir, 'slide09_korea.html'), pptx);
    if (ph9.length > 0) {
        slide9.addChart(pptx.charts.BAR, [{
            name: "Import Change (%)",
            labels: ["Potatoes", "Beef", "Wheat"],
            values: [456.6, 117.4, 65.0]
        }], {
            ...ph9[0],
            barDir: 'bar',
            showTitle: true,
            title: 'Korea Import Growth 2000-2023 (%)',
            titleFontSize: 11,
            showLegend: false,
            showCatAxisTitle: false,
            showValAxisTitle: true,
            valAxisTitle: 'Growth (%)',
            valAxisMinVal: 0,
            valAxisMaxVal: 500,
            chartColors: ["E07A5F"]
        });
    }

    // Slide 10: Conclusion
    await html2pptx(path.join(workDir, 'slide10_conclusion.html'), pptx);

    // Slide 11: Suggestions
    await html2pptx(path.join(workDir, 'slide11_suggestions.html'), pptx);

    // Slide 12: Thank You
    await html2pptx(path.join(workDir, 'slide12_thankyou.html'), pptx);

    // Save
    const outputPath = '/Users/yeong/00_work_out/01_KNU/main_class/MINI_Project/pase4/hamburger/기후변화_햄버거재료_분석_발표.pptx';
    await pptx.writeFile({ fileName: outputPath });
    console.log('Presentation created: ' + outputPath);
}

createPresentation().catch(console.error);
