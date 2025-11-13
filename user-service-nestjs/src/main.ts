import { NestFactory } from '@nestjs/core';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  
  // API versioning prefix
  app.setGlobalPrefix('api/v1');
  
  // Swagger Configuration with explicit settings
  const config = new DocumentBuilder()
    .setTitle('User Service API')
    .setDescription('User management service for the notification system')
    .setVersion('1.0')
    .addTag('users')
    .addTag('health')
    .build();
  
  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('api', app, document);
  
  await app.listen(process.env.PORT ?? 3000);
  console.log(`🚀 User Service running on: http://localhost:${process.env.PORT ?? 3000}`);
  console.log(`📚 Swagger docs: http://localhost:${process.env.PORT ?? 3000}/api`);
  console.log(`📋 API endpoints: http://localhost:${process.env.PORT ?? 3000}/api/v1/users`);
}
void bootstrap();
