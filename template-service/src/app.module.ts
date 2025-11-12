import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { ConfigModule } from '@nestjs/config';
import { TemplatesModule } from './templates/templates.module';

@Module({
imports: [ConfigModule.forRoot({ isGlobal: true }), TemplatesModule],  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
