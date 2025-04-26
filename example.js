const AstrologyImageGenerator = require('./utils/astrology_image_generator');
const fs = require('fs');

async function main() {
    const generator = new AstrologyImageGenerator();
    
    const data = {
        gender: '男',
        trueSolarTime: '农历: 1996年9月3日 7:25',
        lifePalace: '甲午',
        fetalOrigin: '甲午',
        fourPillars: ['丙子', '戊戌', '甲申', '戊辰'],
        fiveElements: [9, 12, 11, 8, 5],
        patternAnalysis: '食伤生财：贫困疾 财格： 印格： 杀印相生： 官杀：最佳 伤官配印：',
        lifeInterpretation: '一句话总结命理；一句话总结命理一句话总结命理一句话总结命理一句话总结命理一句话总结命'
    };

    try {
        const imageBuffer = await generator.generateImage(data);
        fs.writeFileSync('astrology_result.png', imageBuffer);
        console.log('Image generated successfully!');
    } catch (error) {
        console.error('Error generating image:', error);
    }
}

main(); 