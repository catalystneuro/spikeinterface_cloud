import { endpoints } from '../config/endpoints.config';
import axios from 'axios';


export const restApiClient = axios.create({
    baseURL: endpoints?.api ?? '',
    headers: {
        'Content-Type': 'application/json',
    },
})