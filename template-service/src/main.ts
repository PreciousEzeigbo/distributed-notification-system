import { NestFactory } from '@nestjs/core';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  
  // API versioning prefix
  app.setGlobalPrefix('api/v1');
  
  // Swagger Configuration
  const config = new DocumentBuilder()
    .setTitle('Template Service API')
    .setDescription('Template management service for the notification system')
    .setVersion('1.0')
    .addTag('templates')
    .addTag('health')
    .build();
  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('docs', app, document);
  
  await app.listen(process.env.PORT ?? 3000);
  console.log(`🚀 Template Service running on: http://localhost:${process.env.PORT ?? 3000}`);
  console.log(`📚 Swagger docs available at: http://localhost:${process.env.PORT ?? 3000}/docs`);
  console.log(`📋 API endpoints: http://localhost:${process.env.PORT ?? 3000}/api/v1/templates`);
}
bootstrap();
