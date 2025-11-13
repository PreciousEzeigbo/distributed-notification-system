import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export interface Response<T> {
  success: boolean;
  message: string;
  data?: T | null;
  error?: string | null;
  meta?: any | null;
}

@Injectable()
export class ResponseInterceptor<T> implements NestInterceptor<T, Response<T>> {
  intercept(context: ExecutionContext, next: CallHandler): Observable<Response<T>> {
    return next.handle().pipe(
      map(data => {
        // If data is already in the standard format, return it
        if (data && typeof data === 'object' && 'success' in data) {
          return data;
        }

        // Wrap the data in standard format
        return {
          success: true,
          message: this.getDefaultMessage(context),
          data: data || null,
          error: null,
          meta: null,
        };
      }),
    );
  }

  private getDefaultMessage(context: ExecutionContext): string {
    const request = context.switchToHttp().getRequest();
    const method = request.method;
    const path = request.route.path;

    if (method === 'POST') return 'Resource created successfully';
    if (method === 'PUT' || method === 'PATCH') return 'Resource updated successfully';
    if (method === 'DELETE') return 'Resource deleted successfully';
    return 'Operation completed successfully';
  }
}
