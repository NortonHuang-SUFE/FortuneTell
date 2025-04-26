const { createCanvas, loadImage } = require('canvas');
const path = require('path');

class AstrologyImageGenerator {
    constructor() {
        this.canvasWidth = 750;
        this.canvasHeight = 1334;
        this.padding = 40;
        this.sectionGap = 30;
        this.fontFamily = 'Noto Sans SC';
        this.colors = {
            background: '#F2F2F2',
            textPrimary: '#5D5855',
            textSecondary: '#948D89',
            sectionBg: '#EBE8E5',
            sectionBorder: '#FFF6DE',
            buttonBg: '#DCD8D4',
            buttonText: '#9B9490',
            fiveElements: {
                metal: '#FEEAA4',
                wood: '#8CC18A',
                water: '#63C9C3',
                fire: '#B7695E',
                earth: '#948D89'
            }
        };
    }

    async generateImage(data) {
        console.log('开始生成图片...');
        const canvas = createCanvas(this.canvasWidth, this.canvasHeight);
        const ctx = canvas.getContext('2d');

        // Set background
        ctx.fillStyle = this.colors.background;
        ctx.fillRect(0, 0, this.canvasWidth, this.canvasHeight);

        // Draw basic info section
        this.drawBasicInfo(ctx, data);

        // Draw four pillars section
        this.drawFourPillars(ctx, data);

        // Draw five elements section
        this.drawFiveElements(ctx, data);

        // Draw pattern analysis section
        this.drawPatternAnalysis(ctx, data);

        // Draw life interpretation section
        this.drawLifeInterpretation(ctx, data);

        console.log('图片生成完成');
        return canvas.toBuffer('image/png');
    }

    drawBasicInfo(ctx, data) {
        const { gender, trueSolarTime, lifePalace, fetalOrigin } = data;
        let y = this.padding;

        // Draw title
        ctx.font = `bold 40px "${this.fontFamily}"`;
        ctx.fillStyle = this.colors.textPrimary;
        ctx.fillText('基本信息', this.padding, y);
        y += 60;

        // Draw info items
        ctx.font = `bold 30px "${this.fontFamily}"`;
        const items = [
            { label: '性别：', value: gender },
            { label: '命宫：', value: lifePalace },
            { label: '胎元：', value: fetalOrigin },
            { label: '真太阳时：', value: trueSolarTime }
        ];

        items.forEach(item => {
            ctx.fillStyle = this.colors.textPrimary;
            ctx.fillText(item.label, this.padding, y);
            ctx.font = `500 30px "${this.fontFamily}"`;
            ctx.fillText(item.value, this.padding + 120, y);
            ctx.font = `bold 30px "${this.fontFamily}"`;
            y += 50;
        });
    }

    drawFourPillars(ctx, data) {
        const { fourPillars } = data;
        let y = this.padding + 300;

        // Draw section background
        ctx.fillStyle = this.colors.sectionBg;
        ctx.strokeStyle = this.colors.sectionBorder;
        ctx.lineWidth = 2;
        ctx.shadowColor = 'rgba(93, 88, 85, 0.8)';
        ctx.shadowBlur = 6;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 0;
        ctx.fillRect(this.padding, y - 50, this.canvasWidth - 2 * this.padding, 250);
        ctx.strokeRect(this.padding, y - 50, this.canvasWidth - 2 * this.padding, 250);
        ctx.shadowBlur = 0;

        // Draw title
        ctx.font = `500 36px "${this.fontFamily}"`;
        ctx.fillStyle = this.colors.textPrimary;
        ctx.fillText('四柱排盘', this.padding + 20, y);
        y += 60;

        // Draw four pillars
        const pillars = ['年柱', '月柱', '日柱', '时柱'];
        pillars.forEach((pillar, index) => {
            ctx.font = `500 30px "${this.fontFamily}"`;
            ctx.fillStyle = this.colors.textSecondary;
            ctx.fillText(pillar, this.padding + 20, y);
            ctx.font = `bold 40px "${this.fontFamily}"`;
            ctx.fillStyle = this.colors.textPrimary;
            ctx.fillText(fourPillars[index], this.padding + 100, y);
            y += 50;
        });

        // Draw detail button
        this.drawDetailButton(ctx, this.padding + 20, y + 20);
    }

    drawFiveElements(ctx, data) {
        const { fiveElements } = data;
        let y = this.padding + 600;

        // Draw section background
        ctx.fillStyle = this.colors.sectionBg;
        ctx.strokeStyle = this.colors.sectionBorder;
        ctx.lineWidth = 2;
        ctx.shadowColor = 'rgba(93, 88, 85, 0.8)';
        ctx.shadowBlur = 6;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 0;
        ctx.fillRect(this.padding, y - 50, this.canvasWidth - 2 * this.padding, 250);
        ctx.strokeRect(this.padding, y - 50, this.canvasWidth - 2 * this.padding, 250);
        ctx.shadowBlur = 0;

        // Draw title
        ctx.font = `500 36px "${this.fontFamily}"`;
        ctx.fillStyle = this.colors.textPrimary;
        ctx.fillText('五行分数', this.padding + 20, y);
        y += 60;

        // Draw five elements scores
        const elements = [
            { name: '金', color: this.colors.fiveElements.metal },
            { name: '木', color: this.colors.fiveElements.wood },
            { name: '水', color: this.colors.fiveElements.water },
            { name: '火', color: this.colors.fiveElements.fire },
            { name: '土', color: this.colors.fiveElements.earth }
        ];

        elements.forEach((element, index) => {
            ctx.font = `500 24px "${this.fontFamily}"`;
            ctx.fillStyle = this.colors.textPrimary;
            ctx.fillText(`${element.name}：${fiveElements[index]}`, this.padding + 20, y);
            y += 40;
        });

        // Draw detail button
        this.drawDetailButton(ctx, this.padding + 20, y + 20);
    }

    drawPatternAnalysis(ctx, data) {
        const { patternAnalysis } = data;
        let y = this.padding + 800;

        // Draw section background
        ctx.fillStyle = this.colors.sectionBg;
        ctx.strokeStyle = this.colors.sectionBorder;
        ctx.lineWidth = 2;
        ctx.shadowColor = 'rgba(93, 88, 85, 0.8)';
        ctx.shadowBlur = 6;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 0;
        ctx.fillRect(this.padding, y - 50, this.canvasWidth - 2 * this.padding, 200);
        ctx.strokeRect(this.padding, y - 50, this.canvasWidth - 2 * this.padding, 200);
        ctx.shadowBlur = 0;

        // Draw title
        ctx.font = `500 36px "${this.fontFamily}"`;
        ctx.fillStyle = this.colors.textPrimary;
        ctx.fillText('格局分析', this.padding + 20, y);
        y += 60;

        // Draw pattern analysis text
        ctx.font = `500 24px "${this.fontFamily}"`;
        ctx.fillStyle = this.colors.textPrimary;
        ctx.fillText(patternAnalysis, this.padding + 20, y);

        // Draw detail button
        this.drawDetailButton(ctx, this.padding + 20, y + 40);
    }

    drawLifeInterpretation(ctx, data) {
        const { lifeInterpretation } = data;
        let y = this.padding + 1000;

        // Draw section background
        ctx.fillStyle = this.colors.sectionBg;
        ctx.strokeStyle = this.colors.sectionBorder;
        ctx.lineWidth = 2;
        ctx.shadowColor = 'rgba(93, 88, 85, 0.8)';
        ctx.shadowBlur = 6;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 0;
        ctx.fillRect(this.padding, y - 50, this.canvasWidth - 2 * this.padding, 200);
        ctx.strokeRect(this.padding, y - 50, this.canvasWidth - 2 * this.padding, 200);
        ctx.shadowBlur = 0;

        // Draw title
        ctx.font = `500 36px "${this.fontFamily}"`;
        ctx.fillStyle = this.colors.textPrimary;
        ctx.fillText('命理解读', this.padding + 20, y);
        y += 60;

        // Draw life interpretation text
        ctx.font = `500 24px "${this.fontFamily}"`;
        ctx.fillStyle = this.colors.textPrimary;
        ctx.fillText(lifeInterpretation, this.padding + 20, y);

        // Draw detail button
        this.drawDetailButton(ctx, this.padding + 20, y + 40);
    }

    drawDetailButton(ctx, x, y) {
        // Draw button background
        ctx.fillStyle = this.colors.buttonBg;
        ctx.strokeStyle = this.colors.buttonText;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.roundRect(x, y, 120, 40, 31);
        ctx.fill();
        ctx.stroke();

        // Draw button text
        ctx.font = `500 22px "${this.fontFamily}"`;
        ctx.fillStyle = this.colors.buttonText;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('查看详情', x + 60, y + 20);
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';
    }
}

module.exports = AstrologyImageGenerator; 